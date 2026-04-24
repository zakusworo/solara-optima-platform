"""
Unit Commitment and Economic Dispatch MILP Optimizer

Implements mixed-integer linear programming for:
- Generator on/off decisions (unit commitment)
- Power dispatch levels (economic dispatch)
- Solar PV integration
- Battery storage optimization
- Reserve requirements
"""
import pulp as pl
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger

from app.core.config import settings
from app.models.schemas import (
    OptimizationRequest,
    OptimizationResult,
    GeneratorStatus,
    GeneratorData,
)


class UCEDOptimizer:
    """Mixed-Integer Linear Programming optimizer for UC/ED problems"""
    
    def __init__(self, solver_name: str = None, time_limit: int = None):
        self.solver_name = solver_name or settings.SOLVER_NAME
        self.time_limit = time_limit or settings.SOLVER_TIME_LIMIT
        self.model = None
        self.variables = {}
        
    def create_model(self, request: OptimizationRequest) -> pl.LpProblem:
        """Create the MILP model"""
        
        self.model = pl.LpProblem("Unit_Commitment_Economic_Dispatch", pl.LpMinimize)
        self.variables = {}
        
        # Extract data
        T = len(request.load_profile)  # Time periods
        G = len(request.generators)    # Number of generators
        
        time_periods = list(range(T))
        generators = list(range(G))
        
        logger.info(f"Creating optimization model: T={T} periods, G={G} generators")
        
        # Decision variables
        self._create_variables(T, G, request)
        
        # Objective function
        self._create_objective(T, G, request)
        
        # Constraints
        self._create_constraints(T, G, request)
        
        return self.model
    
    def _create_variables(self, T: int, G: int, request: OptimizationRequest):
        """Create decision variables"""
        
        time_periods = list(range(T))
        generators = list(range(G))
        
        # Binary: Generator on/off status
        self.variables['u'] = pl.LpVariable.dicts(
            "UnitStatus",
            ((g, t) for g in generators for t in time_periods),
            cat='Binary',
        )
        
        # Binary: Generator startup
        self.variables['v'] = pl.LpVariable.dicts(
            "Startup",
            ((g, t) for g in generators for t in time_periods),
            cat='Binary',
        )
        
        # Binary: Generator shutdown
        self.variables['w'] = pl.LpVariable.dicts(
            "Shutdown",
            ((g, t) for g in generators for t in time_periods),
            cat='Binary',
        )
        
        # Continuous: Power output
        self.variables['p'] = pl.LpVariable.dicts(
            "PowerOutput",
            ((g, t) for g in generators for t in time_periods),
            lowBound=0,
            cat='Continuous',
        )
        
        # Continuous: Solar power
        if request.solar_forecast:
            self.variables['p_solar'] = pl.LpVariable.dicts(
                "SolarPower",
                (t for t in time_periods),
                lowBound=0,
                upBound=max(request.solar_forecast) if request.solar_forecast else None,
                cat='Continuous',
                
            )
        
        # Continuous: Battery charge/discharge
        if request.bess_capacity > 0:
            self.variables['p_bess_ch'] = pl.LpVariable.dicts(
                "BatteryCharge",
                (t for t in time_periods),
                lowBound=0,
                upBound=request.bess_power_rating,
                cat='Continuous',
                
            )
            self.variables['p_bess_dis'] = pl.LpVariable.dicts(
                "BatteryDischarge",
                (t for t in time_periods),
                lowBound=0,
                upBound=request.bess_power_rating,
                cat='Continuous',
                
            )
            self.variables['soc'] = pl.LpVariable.dicts(
                "StateOfCharge",
                (t for t in time_periods),
                lowBound=request.bess_capacity * request.bess_min_soc,
                upBound=request.bess_capacity * request.bess_max_soc,
                cat='Continuous',
                
            )
            self.variables['bess_mode'] = pl.LpVariable.dicts(
                "BessMode",
                (t for t in time_periods),
                cat='Binary',
            )
        
        # Continuous: Spinning reserve
        self.variables['r'] = pl.LpVariable.dicts(
            "SpinningReserve",
            ((g, t) for g in generators for t in time_periods),
            lowBound=0,
            cat='Continuous',
            
        )
        
        # Continuous: Load shedding (if allowed)
        if request.allow_load_shedding:
            self.variables['ls'] = pl.LpVariable.dicts(
                "LoadShedding",
                (t for t in time_periods),
                lowBound=0,
                upBound=request.load_profile,
                cat='Continuous',
                
            )
    
    def _create_objective(self, T: int, G: int, request: OptimizationRequest):
        """Create objective function: minimize total cost"""
        
        time_periods = list(range(T))
        generators = list(range(G))
        
        objective_terms = []
        
        for g in generators:
            gen = request.generators[g]
            
            for t in time_periods:
                # Fuel cost (linearized quadratic cost curve)
                fuel_cost = gen.fuel_cost * self.variables['p'][(g, t)]
                objective_terms.append(fuel_cost)
                
                # No-load cost
                no_load_cost = gen.no_load_cost * self.variables['u'][(g, t)]
                objective_terms.append(no_load_cost)
                
                # Startup cost
                startup_cost = gen.startup_cost * self.variables['v'][(g, t)]
                objective_terms.append(startup_cost)
                
                # Shutdown cost (if applicable)
                if gen.shutdown_cost > 0:
                    shutdown_cost = gen.shutdown_cost * self.variables['w'][(g, t)]
                    objective_terms.append(shutdown_cost)
                
                # Carbon cost
                if gen.emissions_rate > 0 and settings.CARBON_PRICE > 0:
                    carbon_cost = (gen.emissions_rate * settings.CARBON_PRICE / 1000) * self.variables['p'][(g, t)]
                    objective_terms.append(carbon_cost)
        
        # Battery degradation cost
        if request.bess_capacity > 0:
            for t in time_periods:
                degradation = (
                    self.variables['p_bess_ch'][t] + 
                    self.variables['p_bess_dis'][t]
                ) * request.bess_degradation_cost
                objective_terms.append(degradation)
        
        # Load shedding penalty
        if request.allow_load_shedding:
            for t in time_periods:
                shedding_penalty = request.load_shedding_cost * self.variables['ls'][t]
                objective_terms.append(shedding_penalty)
        
        # Grid electricity cost (if time-of-use pricing)
        if request.tou_prices:
            for t in time_periods:
                grid_cost = request.tou_prices[t] * self.variables.get('p_grid', [0]*T)[t] if 'p_grid' in self.variables else 0
                objective_terms.append(grid_cost)
        
        self.model += pl.lpSum(objective_terms), "Total_Cost"
    
    def _create_constraints(self, T: int, G: int, request: OptimizationRequest):
        """Create all model constraints"""
        
        time_periods = list(range(T))
        generators = list(range(G))
        
        # Power balance constraint
        for t in time_periods:
            supply_terms = [self.variables['p'][(g, t)] for g in generators]
            
            # Add solar
            if request.solar_forecast and 'p_solar' in self.variables:
                supply_terms.append(self.variables['p_solar'][t])
            
            # Add battery discharge
            if request.bess_capacity > 0 and 'p_bess_dis' in self.variables:
                supply_terms.append(self.variables['p_bess_dis'][t])
            
            # Subtract battery charge
            if request.bess_capacity > 0 and 'p_bess_ch' in self.variables:
                supply_terms.append(-self.variables['p_bess_ch'][t])
            
            # Load shedding
            if request.allow_load_shedding and 'ls' in self.variables:
                demand = request.load_profile[t] - self.variables['ls'][t]
            else:
                demand = request.load_profile[t]
            
            self.model += pl.lpSum(supply_terms) == demand, f"PowerBalance_{t}"
        
        # Generator limits
        for g in generators:
            gen = request.generators[g]
            for t in time_periods:
                # Min/max output
                self.model += (
                    self.variables['p'][(g, t)] >= gen.min_output * self.variables['u'][(g, t)],
                    f"MinOutput_{g}_{t}"
                )
                self.model += (
                    self.variables['p'][(g, t)] <= gen.max_output * self.variables['u'][(g, t)],
                    f"MaxOutput_{g}_{t}"
                )
                
                # Ramp up
                if t > 0:
                    self.model += (
                        self.variables['p'][(g, t)] - self.variables['p'][(g, t-1)] <= gen.ramp_up,
                        f"RampUp_{g}_{t}"
                    )
                else:
                    self.model += (
                        self.variables['p'][(g, t)] - gen.initial_output <= gen.ramp_up,
                        f"RampUp_{g}_{t}"
                    )
                
                # Ramp down
                if t > 0:
                    self.model += (
                        self.variables['p'][(g, t-1)] - self.variables['p'][(g, t)] <= gen.ramp_down,
                        f"RampDown_{g}_{t}"
                    )
                else:
                    self.model += (
                        gen.initial_output - self.variables['p'][(g, t)] <= gen.ramp_down,
                        f"RampDown_{g}_{t}"
                    )
        
        # Minimum up/down time
        for g in generators:
            gen = request.generators[g]
            if gen.min_uptime > 1 or gen.min_downtime > 1:
                self._add_min_up_down_constraints(g, T, gen)
        
        # Startup/shutdown logic
        for g in generators:
            for t in time_periods:
                if t > 0:
                    self.model += (
                        self.variables['u'][(g, t)] - self.variables['u'][(g, t-1)] == 
                        self.variables['v'][(g, t)] - self.variables['w'][(g, t)],
                        f"StartupShutdown_{g}_{t}"
                    )
                else:
                    self.model += (
                        self.variables['u'][(g, t)] - gen.initial_status == 
                        self.variables['v'][(g, t)] - self.variables['w'][(g, t)],
                        f"StartupShutdown_{g}_{t}"
                    )
                
                # Cannot startup and shutdown simultaneously
                self.model += (
                    self.variables['v'][(g, t)] + self.variables['w'][(g, t)] <= 1,
                    f"NoSimultaneousStartStop_{g}_{t}"
                )
        
        # Spinning reserve requirement
        for t in time_periods:
            reserve_required = request.load_profile[t] * (
                settings.SPINNING_RESERVE_PCT / 100 +
                settings.OPERATING_RESERVE_PCT / 100 +
                settings.LOAD_UNCERTAINTY_PCT / 100
            )
            
            reserve_terms = []
            for g in generators:
                gen = request.generators[g]
                # Available reserve = max output - current output (if online)
                reserve_terms.append(
                    (gen.max_output - gen.min_output) * self.variables['u'][(g, t)] - 
                    self.variables['r'][(g, t)]
                )
            
            self.model += pl.lpSum(reserve_terms) >= reserve_required, f"SpinningReserve_{t}"
        
        # Battery constraints
        if request.bess_capacity > 0 and 'soc' in self.variables:
            for t in time_periods:
                # SOC dynamics
                if t > 0:
                    self.model += (
                        self.variables['soc'][t] == 
                        self.variables['soc'][t-1] + 
                        self.variables['p_bess_ch'][t] * request.bess_efficiency -
                        self.variables['p_bess_dis'][t] * (1.0 / request.bess_efficiency),
                        f"BatteryDynamics_{t}"
                    )
                else:
                    self.model += (
                        self.variables['soc'][t] == 
                        request.bess_capacity * request.bess_initial_soc + 
                        self.variables['p_bess_ch'][t] * request.bess_efficiency -
                        self.variables['p_bess_dis'][t] * (1.0 / request.bess_efficiency),
                        f"BatteryDynamics_{t}"
                    )
                # No simultaneous charge/discharge (relaxed with big-M)
                self.model += (
                    self.variables['p_bess_ch'][t] <= request.bess_power_rating * self.variables['bess_mode'][t],
                    f"ChargeMode_{t}"
                )
                self.model += (
                    self.variables['p_bess_dis'][t] <= request.bess_power_rating * (1 - self.variables['bess_mode'][t]),
                    f"DischargeMode_{t}"
                )
            
            # End-of-horizon SOC constraint (optional)
            if request.bess_final_soc is not None:
                self.model += (
                    self.variables['soc'][T-1] >= request.bess_capacity * request.bess_final_soc,
                    "FinalSOC"
                )
        
        # Solar constraints
        if request.solar_forecast and 'p_solar' in self.variables:
            for t in time_periods:
                self.model += (
                    self.variables['p_solar'][t] <= request.solar_forecast[t],
                    f"SolarLimit_{t}"
                )
    
    def _add_min_up_down_constraints(self, g: int, T: int, gen: GeneratorData):
        """Add minimum uptime and downtime constraints"""
        
        if gen.min_uptime > 1:
            for t in range(T):
                if t >= gen.min_uptime - 1:
                    # Sum of startups in last min_uptime periods <= current status
                    self.model += (
                        pl.lpSum(self.variables['v'][(g, tau)] for tau in range(t - gen.min_uptime + 1, t + 1)) <=
                        self.variables['u'][(g, t)],
                        f"MinUptime_{g}_{t}"
                    )
        
        if gen.min_downtime > 1:
            for t in range(T):
                if t >= gen.min_downtime - 1:
                    # Sum of shutdowns in last min_downtime periods <= 1 - current status
                    self.model += (
                        pl.lpSum(self.variables['w'][(g, tau)] for tau in range(t - gen.min_downtime + 1, t + 1)) <=
                        1 - self.variables['u'][(g, t)],
                        f"MinDowntime_{g}_{t}"
                    )
    
    def solve(self) -> Optional[OptimizationResult]:
        """Solve the optimization problem"""
        
        logger.info(f"Solving with {self.solver_name} solver (time limit: {self.time_limit}s)")
        
        # Select solver
        if self.solver_name.lower() == 'cbc':
            solver = pl.PULP_CBC_CMD(
                msg=settings.DEBUG,
                timeLimit=self.time_limit,
                gapRel=0.01,  # 1% optimality gap
            )
        elif self.solver_name.lower() == 'glpk':
            solver = pl.GLPK(msg=settings.DEBUG, timeLimit=self.time_limit)
        else:
            logger.warning(f"Unknown solver '{self.solver_name}', using CBC")
            solver = pl.PULP_CBC_CMD(msg=settings.DEBUG, timeLimit=self.time_limit)
        
        # Solve
        self.model.solve(solver)
        
        # Check status
        status = pl.LpStatus[self.model.status]
        logger.info(f"Optimization status: {status}")
        
        if self.model.status != pl.LpStatusOptimal:
            logger.warning(f"Optimization did not converge to optimal solution: {status}")
        
        # Extract solution
        return self._extract_solution()
    
    def _extract_solution(self) -> Optional[OptimizationResult]:
        """Extract solution from model variables"""
        
        T = max(t for (_, t) in self.variables['u'].keys()) + 1
        G = max(g for (g, _) in self.variables['u'].keys()) + 1
        
        # Generator schedules
        generator_schedules = []
        for g in range(G):
            schedule = {
                'generator_id': g,
                'status': [],
                'output': [],
                'startup': [],
                'shutdown': [],
                'reserve': [],
            }
            for t in range(T):
                schedule['status'].append(int(pl.value(self.variables['u'][(g, t)])))
                schedule['output'].append(pl.value(self.variables['p'][(g, t)]) or 0)
                schedule['startup'].append(int(pl.value(self.variables['v'][(g, t)])))
                schedule['shutdown'].append(int(pl.value(self.variables['w'][(g, t)])))
                schedule['reserve'].append(pl.value(self.variables['r'][(g, t)]) or 0)
            generator_schedules.append(schedule)
        
        # Solar output
        solar_output = None
        if 'p_solar' in self.variables:
            solar_output = [pl.value(self.variables['p_solar'][t]) or 0 for t in range(T)]
        
        # Battery operation
        battery_operation = None
        if 'soc' in self.variables:
            battery_operation = {
                'charge': [pl.value(self.variables['p_bess_ch'][t]) or 0 for t in range(T)],
                'discharge': [pl.value(self.variables['p_bess_dis'][t]) or 0 for t in range(T)],
                'soc': [pl.value(self.variables['soc'][t]) or 0 for t in range(T)],
            }
        
        # Calculate costs
        total_cost = pl.value(self.model.objective) or 0
        fuel_cost = sum(
            pl.value(self.variables['p'][(g, t)]) * 0  # Simplified
            for g in range(G) for t in range(T)
        )
        
        # Calculate emissions
        total_emissions = 0  # Calculate from generator outputs
        
        return OptimizationResult(
            status=pl.LpStatus[self.model.status],
            total_cost=total_cost,
            generator_schedules=generator_schedules,
            solar_output=solar_output,
            battery_operation=battery_operation,
            load_served=[pl.value(self.model.constraints[f"PowerBalance_{t}"].constant) or 0 for t in range(T)],
            emissions=total_emissions,
            solve_time=self.model.solutionTime,
        )


def run_optimization(request: OptimizationRequest) -> OptimizationResult:
    """Main function to run UC/ED optimization"""
    
    optimizer = UCEDOptimizer(
        solver_name=request.solver_name if hasattr(request, 'solver_name') else None,
        time_limit=request.time_limit if hasattr(request, 'time_limit') else None,
    )
    
    optimizer.create_model(request)
    result = optimizer.solve()
    
    return result
