import { useState, useEffect } from 'react'
import {
  Calculator,
  Sun,
  Leaf,
  Wallet,
  TrendingUp,
  Building2,
  Banknote,
  Send,
  CheckCircle2,
  Loader2,
} from 'lucide-react'
import Plot from 'react-plotly.js'
import { api } from '../utils/api'

interface Tariff {
  code: string
  name: string
  segment: string
  price_idr_per_kwh: number
}

const PROVINCES = [
  '', 'DKI Jakarta', 'Jawa Barat', 'Banten', 'Jawa Tengah', 'DI Yogyakarta',
  'Jawa Timur', 'Bali', 'Nusa Tenggara Barat', 'Nusa Tenggara Timur',
  'Sumatera Utara', 'Riau', 'Sumatera Barat', 'Sulawesi Selatan',
]

const fmtIDR = (v: number) =>
  new Intl.NumberFormat('id-ID', { maximumFractionDigits: 0 }).format(Math.round(v || 0))

// Compact IDR: juta / milyar
const fmtShort = (v: number) => {
  const n = v || 0
  if (Math.abs(n) >= 1e9) return `Rp ${(n / 1e9).toFixed(2)} M`
  if (Math.abs(n) >= 1e6) return `Rp ${(n / 1e6).toFixed(1)} jt`
  return `Rp ${fmtIDR(n)}`
}

export default function Marketplace() {
  // ----- form state -----
  const [inputMode, setInputMode] = useState<'bill' | 'capacity'>('bill')
  const [monthlyBill, setMonthlyBill] = useState(25000000)
  const [capacity, setCapacity] = useState(100)
  const [tariffCode, setTariffCode] = useState('B-2/TR-6600-200k')
  const [segment, setSegment] = useState('commercial')
  const [region, setRegion] = useState('Jawa Barat')
  const [roofArea, setRoofArea] = useState<number | ''>(800)

  const [tariffs, setTariffs] = useState<Tariff[]>([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [match, setMatch] = useState<any>(null)

  // ----- quote form state -----
  const [showQuote, setShowQuote] = useState(false)
  const [quote, setQuote] = useState({ name: '', email: '', phone: '', company: '' })
  const [quoteResult, setQuoteResult] = useState<string | null>(null)

  useEffect(() => {
    api.get('/api/v1/marketplace/tariffs')
      .then((r) => setTariffs(r.data.data || []))
      .catch(() => setTariffs([]))
  }, [])

  const runEstimate = async () => {
    setLoading(true)
    setResult(null)
    setMatch(null)
    setQuoteResult(null)
    try {
      const payload: any = { tariff_code: tariffCode, segment }
      if (inputMode === 'bill') payload.monthly_bill_idr = monthlyBill
      else payload.desired_capacity_kwp = capacity
      if (roofArea !== '') payload.roof_area_m2 = roofArea

      const res = await api.post('/api/v1/marketplace/estimate', payload)
      const data = res.data.data
      setResult(data)

      const m = await api.post('/api/v1/marketplace/match', {
        capacity_kwp: data.recommended_capacity_kwp,
        capex_idr: data.capex_idr,
        segment,
        region: region || undefined,
        limit: 5,
      })
      setMatch(m.data.data)
    } catch (e) {
      console.error(e)
      alert('Estimate failed. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const submitQuote = async () => {
    if (!quote.name || !quote.email) {
      alert('Please enter your name and email.')
      return
    }
    try {
      const res = await api.post('/api/v1/marketplace/quote-request', {
        ...quote,
        segment,
        region: region || undefined,
        capacity_kwp: result?.recommended_capacity_kwp,
        monthly_bill_idr: inputMode === 'bill' ? monthlyBill : undefined,
      })
      setQuoteResult(res.data.data.lead_id)
    } catch (e) {
      alert('Could not submit quote request.')
    }
  }

  const kpis = result
    ? [
        { label: 'Recommended size', value: `${result.recommended_capacity_kwp} kWp`, sub: `${result.num_panels_estimate} panels`, icon: Sun },
        { label: 'Annual bill saving', value: fmtShort(result.annual_bill_saving_idr), sub: `LCOE Rp ${fmtIDR(result.lcoe_idr_per_kwh)}/kWh`, icon: Wallet },
        { label: 'Payback', value: result.payback_years != null ? `${result.payback_years} yrs` : '—', sub: `IRR ${result.irr_pct ?? '—'}%`, icon: TrendingUp },
        { label: '25-yr net saving', value: fmtShort(result.lifetime_net_saving_idr), sub: `NPV ${fmtShort(result.npv_idr)}`, icon: Banknote },
        { label: 'CO₂ avoided', value: `${result.annual_co2_avoided_tonnes} t/yr`, sub: `${result.trees_equivalent_per_year} trees/yr`, icon: Leaf },
      ]
    : []

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">Solar Marketplace &amp; Financing</h1>
        <p className="text-[#8A7A60] mt-1">
          Size a rooftop system from your PLN bill, see bankable savings &amp; CO₂ impact,
          and get matched to installers and financing.
        </p>
      </div>

      {/* Input form */}
      <div className="bg-white rounded-xl border border-[#C8BFA8] p-5 space-y-4">
        <div className="flex gap-2">
          <button
            onClick={() => setInputMode('bill')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${inputMode === 'bill' ? 'bg-[#3A7010] text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            From my bill
          </button>
          <button
            onClick={() => setInputMode('capacity')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${inputMode === 'capacity' ? 'bg-[#3A7010] text-white' : 'bg-gray-100 text-gray-700'}`}
          >
            From target size
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {inputMode === 'bill' ? (
            <div>
              <label className="text-sm font-medium">Monthly bill (IDR)</label>
              <input
                type="number"
                value={monthlyBill}
                onChange={(e) => setMonthlyBill(Number(e.target.value))}
                className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
              />
            </div>
          ) : (
            <div>
              <label className="text-sm font-medium">Target size (kWp)</label>
              <input
                type="number"
                value={capacity}
                onChange={(e) => setCapacity(Number(e.target.value))}
                className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
              />
            </div>
          )}

          <div>
            <label className="text-sm font-medium">PLN tariff</label>
            <select
              value={tariffCode}
              onChange={(e) => setTariffCode(e.target.value)}
              className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              {tariffs.map((t) => (
                <option key={t.code} value={t.code}>
                  {t.name} — Rp {fmtIDR(t.price_idr_per_kwh)}/kWh
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Segment</label>
            <select
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
              className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              <option value="residential">Residential</option>
              <option value="commercial">Commercial / SME</option>
              <option value="industrial">Industrial</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Province</label>
            <select
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            >
              {PROVINCES.map((p) => (
                <option key={p} value={p}>{p === '' ? 'Any / nationwide' : p}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium">Roof area (m²)</label>
            <input
              type="number"
              value={roofArea}
              onChange={(e) => setRoofArea(e.target.value === '' ? '' : Number(e.target.value))}
              placeholder="optional"
              className="mt-2 w-full px-3 py-2 border border-[#C8BFA8] rounded-lg focus:outline-none focus:ring-2 focus:ring-[#3A7010]"
            />
          </div>
        </div>

        <button
          onClick={runEstimate}
          disabled={loading}
          className="flex items-center gap-2 px-6 py-3 bg-[#3A7010] text-white rounded-lg font-medium hover:bg-[#2D6010] disabled:opacity-50"
        >
          {loading ? <Loader2 size={20} className="animate-spin" /> : <Calculator size={20} />}
          {loading ? 'Calculating…' : 'Get Solar Estimate'}
        </button>
      </div>

      {result && (
        <>
          {/* KPI cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {kpis.map((k) => {
              const Icon = k.icon
              return (
                <div key={k.label} className="bg-white rounded-xl border border-[#C8BFA8] p-4">
                  <div className="flex items-center gap-2 text-[#8A7A60]">
                    <Icon size={16} />
                    <p className="text-xs uppercase">{k.label}</p>
                  </div>
                  <p className="text-xl font-semibold mt-2 text-[#3A7A18]">{k.value}</p>
                  <p className="text-xs text-[#8A7A60] mt-1">{k.sub}</p>
                </div>
              )
            })}
          </div>

          {/* Bankability + roof note */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-4 flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-3">
              <span className="text-sm text-[#8A7A60]">Bankability score</span>
              <div className="w-40 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-[#3A7010]"
                  style={{ width: `${result.bankability_score}%` }}
                />
              </div>
              <span className="font-semibold">{result.bankability_score}/100</span>
            </div>
            {result.roof_limited && (
              <span className="text-sm text-amber-700 bg-amber-50 px-3 py-1 rounded-lg">
                Size capped by available roof area ({result.roof_area_required_m2} m² used)
              </span>
            )}
            <span className="text-sm text-[#8A7A60]">
              Annual generation: <strong>{fmtIDR(result.annual_generation_kwh)} kWh</strong>
              {' · '}Self-consumed: <strong>{fmtIDR(result.annual_self_consumed_kwh)} kWh</strong>
            </span>
          </div>

          {/* Financing options */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-5">
            <h3 className="font-semibold text-lg mb-3">Financing options</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[#8A7A60] border-b border-[#E4DDD0]">
                    <th className="py-2 pr-4">Option</th>
                    <th className="py-2 pr-4">Upfront</th>
                    <th className="py-2 pr-4">Monthly</th>
                    <th className="py-2 pr-4">Payback</th>
                    <th className="py-2 pr-4">IRR</th>
                    <th className="py-2 pr-4">25-yr net</th>
                    <th className="py-2 pr-4">NPV</th>
                  </tr>
                </thead>
                <tbody>
                  {result.financing_options.map((o: any) => (
                    <tr key={o.type} className="border-b border-[#F0EBE0]">
                      <td className="py-3 pr-4">
                        <div className="font-medium">{o.label}</div>
                        <div className="text-xs text-[#8A7A60] max-w-xs">{o.description}</div>
                      </td>
                      <td className="py-3 pr-4">{fmtShort(o.upfront_cost_idr)}</td>
                      <td className="py-3 pr-4">{o.monthly_payment_idr ? fmtShort(o.monthly_payment_idr) : '—'}</td>
                      <td className="py-3 pr-4">{o.payback_years != null ? `${o.payback_years} yrs` : '—'}</td>
                      <td className="py-3 pr-4">{o.irr_pct != null ? `${o.irr_pct}%` : '—'}</td>
                      <td className="py-3 pr-4 font-medium text-[#3A7A18]">{fmtShort(o.lifetime_net_saving_idr)}</td>
                      <td className="py-3 pr-4">{fmtShort(o.npv_idr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Cashflow chart */}
          <div className="bg-white rounded-xl border border-[#C8BFA8] p-6">
            <h3 className="font-semibold mb-4">Cumulative cashflow — cash purchase (Rp juta)</h3>
            <div className="h-72">
              <Plot
                data={[
                  {
                    x: result.cashflow_years,
                    y: result.cumulative_cashflow_cash_idr.map((v: number) => v / 1e6),
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: '#3A7A18', width: 3 },
                    name: 'Cumulative (Rp juta)',
                    fill: 'tozeroy',
                    fillcolor: 'rgba(58,122,24,0.08)',
                  },
                ]}
                layout={{
                  margin: { t: 20, b: 40, l: 60, r: 20 },
                  xaxis: { title: 'Year' },
                  yaxis: { title: 'Rp juta', zeroline: true, zerolinecolor: '#B04030' },
                  showlegend: false,
                }}
                config={{ responsive: true, displayModeBar: false }}
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          </div>

          {/* Matches */}
          {match && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-[#C8BFA8] p-5">
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <Building2 size={18} /> Matched installers
                </h3>
                <div className="space-y-3">
                  {match.installers.length === 0 && (
                    <p className="text-sm text-[#8A7A60]">No installer match for this size/region.</p>
                  )}
                  {match.installers.map((i: any) => (
                    <div key={i.id} className="border border-[#E4DDD0] rounded-lg p-3">
                      <div className="flex justify-between items-start">
                        <div className="font-medium">{i.name}</div>
                        <div className="text-sm text-[#A07010]">★ {i.rating}</div>
                      </div>
                      <div className="text-xs text-[#8A7A60] mt-1">{i.offering}</div>
                      <div className="text-xs text-[#8A7A60] mt-1">
                        {i.min_kwp}–{i.max_kwp} kWp · {i.projects_completed} projects · {i.lead_time_weeks}w lead time
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-xl border border-[#C8BFA8] p-5">
                <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                  <Banknote size={18} /> Matched financing
                </h3>
                <div className="space-y-3">
                  {match.financiers.length === 0 && (
                    <p className="text-sm text-[#8A7A60]">No financing match for this segment/ticket.</p>
                  )}
                  {match.financiers.map((f: any) => (
                    <div key={f.id} className="border border-[#E4DDD0] rounded-lg p-3">
                      <div className="flex justify-between items-start">
                        <div className="font-medium">{f.name}</div>
                        <div className="text-xs px-2 py-0.5 rounded bg-[#EDE8DC] text-[#5A4E3A]">{f.type}</div>
                      </div>
                      <div className="text-xs text-[#8A7A60] mt-1">{f.description}</div>
                      <div className="text-xs text-[#8A7A60] mt-1">
                        {f.provider_kind}
                        {f.interest_rate != null && ` · ${(f.interest_rate * 100).toFixed(1)}%/yr`}
                        {f.tenor_months_max != null && ` · up to ${f.tenor_months_max} mo`}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Quote CTA */}
          <div className="bg-[#EDE8DC] rounded-xl border border-[#C8BFA8] p-5">
            {quoteResult ? (
              <div className="flex items-center gap-3 text-[#3A7010]">
                <CheckCircle2 size={22} />
                <span>
                  Request received — reference <strong>{quoteResult}</strong>. A partner will reach out.
                </span>
              </div>
            ) : !showQuote ? (
              <div className="flex items-center justify-between flex-wrap gap-3">
                <p className="text-[#5A4E3A]">
                  Like these numbers? Request quotes from matched installers &amp; financiers.
                </p>
                <button
                  onClick={() => setShowQuote(true)}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#3A7010] text-white rounded-lg font-medium hover:bg-[#2D6010]"
                >
                  <Send size={18} /> Request quotes
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                <h3 className="font-semibold">Request quotes</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <input placeholder="Name*" value={quote.name}
                    onChange={(e) => setQuote({ ...quote, name: e.target.value })}
                    className="px-3 py-2 border border-[#C8BFA8] rounded-lg" />
                  <input placeholder="Email*" value={quote.email}
                    onChange={(e) => setQuote({ ...quote, email: e.target.value })}
                    className="px-3 py-2 border border-[#C8BFA8] rounded-lg" />
                  <input placeholder="Phone" value={quote.phone}
                    onChange={(e) => setQuote({ ...quote, phone: e.target.value })}
                    className="px-3 py-2 border border-[#C8BFA8] rounded-lg" />
                  <input placeholder="Company" value={quote.company}
                    onChange={(e) => setQuote({ ...quote, company: e.target.value })}
                    className="px-3 py-2 border border-[#C8BFA8] rounded-lg" />
                </div>
                <button
                  onClick={submitQuote}
                  className="flex items-center gap-2 px-5 py-2.5 bg-[#3A7010] text-white rounded-lg font-medium hover:bg-[#2D6010]"
                >
                  <Send size={18} /> Submit
                </button>
              </div>
            )}
          </div>

          <p className="text-xs text-[#8A7A60]">
            Estimates are illustrative and not a financial guarantee. Assumptions:
            specific yield {result.assumptions.specific_yield_kwh_per_kwp} kWh/kWp/yr,
            grid factor {result.assumptions.grid_emission_factor_kg_per_kwh} kgCO₂/kWh,
            discount rate {(result.assumptions.discount_rate * 100).toFixed(0)}%.
          </p>
        </>
      )}
    </div>
  )
}
