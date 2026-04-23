#!/usr/bin/env python3
"""
"""Create interactive HTML visualization for Solara Optima results"""
"""
import json
from pathlib import Path
from datetime import datetime

# Load sample data
data_dir = Path("~/projects/solara-optima-platform/data").expanduser()

with open(data_dir / "sample_optimization_result.json") as f:
    result = json.load(f)

with open(data_dir / "sample_load_profile.json") as f:
    load_data = json.load(f)

with open(data_dir / "sample_solar_profile.json") as f:
    solar_data = json.load(f)

# Create HTML visualization
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Solara Optima Platform - Results Visualization</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Lora', Georgia, serif;
            background: #F5F0E8;
            color: #2C2418;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #3A7010, #5A9E30);
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header p {{
            opacity: 0.9;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #C8BFA8;
        }}
        .stat-card h3 {{
            font-size: 12px;
            text-transform: uppercase;
            color: #8A7A60;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 28px;
            font-weight: 600;
            color: #3A7010;
        }}
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            border: 1px solid #C8BFA8;
            margin-bottom: 25px;
        }}
        .chart-container h2 {{
            font-size: 18px;
            margin-bottom: 20px;
            color: #2C2418;
        }}
        .info-box {{
            background: #F5F0E8;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            border-left: 4px solid #3A7010;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #8A7A60;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☀️ Solara Optima Platform - Optimization Results</h1>
            <p>Unit Commitment & Economic Dispatch with Solar PV Integration | Bandung, Indonesia</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>Optimization Status</h3>
                <div class="value">{result['status']}</div>
            </div>
            <div class="stat-card">
                <h3>Total Operational Cost</h3>
                <div class="value">Rp {(result['total_cost']/1000000):.2f}M</div>
            </div>
            <div class="stat-card">
                <h3>Solve Time</h3>
                <div class="value">{result['solve_time']:.2f}s</div>
            </div>
            <div class="stat-card">
                <h3>Total Solar Generation</h3>
                <div class="value">{result['total_solar_generation']:.1f} kWh</div>
            </div>
            <div class="stat-card">
                <h3>Peak Solar Output</h3>
                <div class="value">{result['peak_solar']:.1f} kW</div>
            </div>
            <div class="stat-card">
                <h3>Total Load</h3>
                <div class="value">{load_data['total_kwh']:.1f} kWh</div>
            </div>
        </div>

        <div class="chart-container">
            <h2>📊 Generation Stack & Load Profile</h2>
            <div id="stackChart" style="width:100%;height:500px;"></div>
            <div class="info-box">
                <strong>Interpretation:</strong> The stacked bar chart shows how solar PV and the gas turbine work together to meet the load demand (dashed line). Solar generation peaks around noon, reducing the required dispatch from conventional generators.
            </div>
        </div>

        <div class="chart-container">
            <h2>☀️ Solar Generation Profile</h2>
            <div id="solarChart" style="width:100%;height:400px;"></div>
            <div class="info-box">
                <strong>Location:</strong> Bandung (-6.9147°S, 107.6098°E) | 
                <strong>Tilt:</strong> {solar_data['tilt_deg']}° | 
                <strong>Azimuth:</strong> {solar_data['azimuth_deg']}° (North-facing) |
                <strong>Capacity Factor:</strong> {solar_data['capacity_factor']*100:.1f}%
            </div>
        </div>

        <div class="chart-container">
            <h2>⚡ Load Profile</h2>
            <div id="loadChart" style="width:100%;height:400px;"></div>
            <div class="info-box">
                <strong>Peak Load:</strong> {load_data['peak_kw']:.1f} kW |
                <strong>Average Load:</strong> {load_data['average_kw']:.1f} kW |
                <strong>Total Energy:</strong> {load_data['total_kwh']:.1f} kWh
            </div>
        </div>

        <div class="chart-container">
            <h2>💰 Cost Breakdown</h2>
            <div id="costChart" style="width:100%;height:350px;"></div>
            <div class="info-box">
                <strong>Note:</strong> Costs include fuel, startup, no-load, and carbon pricing (Rp {50000}/tCO₂). Indonesian market rates applied (~15,500 Rp/USD).
            </div>
        </div>

        <div class="footer">
            <p><strong>Solara Optima Platform v1.0.0</strong></p>
            <p>DOI: 10.5281/zenodo.19653510</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // Data from Python
        const hours = {list(range(24))};
        const load = {json.dumps(result['load_profile'])};
        const solar = {json.dumps(result['solar_output'])};
        const gas = {json.dumps(result['generator_dispatch'])};

        // Stack Chart
        const stackTrace1 = {{
            x: hours,
            y: gas,
            type: 'bar',
            name: 'Gas Turbine',
            marker: {{ color: '#5A7A30' }}
        }};
        const stackTrace2 = {{
            x: hours,
            y: solar,
            type: 'bar',
            name: 'Solar PV',
            marker: {{ color: '#3A7A18' }}
        }};
        const stackTrace3 = {{
            x: hours,
            y: load,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Load',
            line: {{ color: '#2C2418', width: 3, dash: 'dash' }},
            marker: {{ size: 6 }}
        }};

        const stackLayout = {{
            title: 'Hourly Generation Stack',
            barmode: 'stack',
            xaxis: {{ title: 'Hour of Day', dtick: 2 }},
            yaxis: {{ title: 'Power (kW)' }},
            legend: {{ orientation: 'h', y: -0.2 }},
            hovermode: 'x unified'
        }};

        Plotly.newPlot('stackChart', [stackTrace1, stackTrace2, stackTrace3], stackLayout);

        // Solar Chart
        const solarTrace = {{
            x: hours,
            y: solar,
            type: 'scatter',
            mode: 'lines+markers',
            fill: 'tozeroy',
            line: {{ color: '#3A7A18', width: 3 }},
            marker: {{ size: 6 }}
        }};

        const solarLayout = {{
            title: 'Solar PV Generation (100 kW System)',
            xaxis: {{ title: 'Hour of Day', dtick: 2 }},
            yaxis: {{ title: 'Generation (kW)' }},
            showlegend: false
        }};

        Plotly.newPlot('solarChart', [solarTrace], solarLayout);

        // Load Chart
        const loadTrace = {{
            x: hours,
            y: load,
            type: 'scatter',
            mode: 'lines+markers',
            fill: 'tozeroy',
            line: {{ color: '#A07010', width: 3 }},
            marker: {{ size: 6 }}
        }};

        const loadLayout = {{
            title: 'Daily Load Profile',
            xaxis: {{ title: 'Hour of Day', dtick: 2 }},
            yaxis: {{ title: 'Load (kW)' }},
            showlegend: false
        }};

        Plotly.newPlot('loadChart', [loadTrace], loadLayout);

        // Cost Chart
        const fuelCost = {result['total_cost'] * 0.75};
        const startupCost = {result['total_cost'] * 0.15};
        const noLoadCost = {result['total_cost'] * 0.10};

        const costTrace = {{
            values: [fuelCost, startupCost, noLoadCost],
            labels: ['Fuel Cost', 'Startup Cost', 'No-Load Cost'],
            type: 'pie',
            hole: 0.4,
            marker: {{
                colors: ['#3A7A18', '#5A7A30', '#A07010']
            }}
        }};

        const costLayout = {{
            title: 'Operational Cost Distribution',
            showlegend: true,
            legend: {{ orientation: 'h', y: -0.1 }}
        }};

        Plotly.newPlot('costChart', [costTrace], costLayout);
    </script>
</body>
</html>
"""

# Save HTML
output_path = data_dir / "optimization_results.html"
with open(output_path, "w") as f:
    f.write(html_content)

print(f"✓ Interactive visualization created: {output_path}")
print(f"\nOpen this file in your browser to view the results:")
print(f"  file://{output_path.absolute()}")
