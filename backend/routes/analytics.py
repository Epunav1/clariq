"""
Advanced Analytics API Routes

Endpoints for predictive analytics, cohort analysis, churn prediction, and benchmarking
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, List, Optional
from db.advanced_analytics import advanced_analytics
from db.pilots_db import list_pilots

router = APIRouter()


class ForecastRequest(BaseModel):
    pilot_id: int
    days: int = 30
    metric: str = "roi"  # roi, revenue


class CohortDefinition(BaseModel):
    name: str
    definition: Dict


class BenchmarkQuery(BaseModel):
    pilot_id: int


@router.post("/forecast")
async def forecast_metrics(request: ForecastRequest) -> Dict:
    """Forecast ROI or revenue for a pilot"""
    if request.metric == "roi":
        return advanced_analytics.forecast_roi(request.pilot_id, request.days)
    elif request.metric == "revenue":
        return advanced_analytics.forecast_revenue(request.pilot_id, request.days)
    else:
        raise HTTPException(status_code=400, detail="Invalid metric")


@router.get("/forecast/{pilot_id}")
async def get_forecast(pilot_id: int, days: int = Query(30)) -> Dict:
    """Get ROI forecast for a pilot"""
    return advanced_analytics.forecast_roi(pilot_id, days)


@router.get("/forecast/{pilot_id}/revenue")
async def get_revenue_forecast(pilot_id: int, days: int = Query(30)) -> Dict:
    """Get revenue forecast for a pilot"""
    return advanced_analytics.forecast_revenue(pilot_id, days)


@router.post("/cohorts")
async def create_cohort(cohort: CohortDefinition) -> Dict:
    """Create a new pilot cohort based on criteria"""
    return advanced_analytics.create_cohort(cohort.name, cohort.definition)


@router.get("/cohorts/{name}")
async def get_cohort_analysis(name: str) -> Dict:
    """Analyze a cohort's metrics"""
    return advanced_analytics.analyze_cohort(name)


@router.get("/cohorts")
async def list_cohorts() -> List[Dict]:
    """List all defined cohorts"""
    # TODO: Implement cohort listing
    return []


@router.get("/churn/{pilot_id}")
async def predict_churn(pilot_id: int) -> Dict:
    """Predict churn risk for a pilot"""
    return advanced_analytics.predict_churn_risk(pilot_id)


@router.post("/churn/check-all")
async def check_all_churn() -> Dict:
    """Check churn risk for all pilots"""
    pilots = list_pilots()
    at_risk = []
    medium_risk = []
    low_risk = []
    
    for pilot in pilots:
        prediction = advanced_analytics.predict_churn_risk(pilot['id'])
        if prediction.get('churn_risk_level') == 'high':
            at_risk.append(prediction)
        elif prediction.get('churn_risk_level') == 'medium':
            medium_risk.append(prediction)
        else:
            low_risk.append(prediction)
    
    return {
        'total_pilots': len(pilots),
        'at_risk_count': len(at_risk),
        'medium_risk_count': len(medium_risk),
        'low_risk_count': len(low_risk),
        'at_risk': at_risk,
        'medium_risk': medium_risk
    }


@router.get("/benchmark/{pilot_id}")
async def get_benchmark(pilot_id: int) -> Dict:
    """Benchmark a pilot against peer average"""
    return advanced_analytics.benchmark_pilot(pilot_id)


@router.get("/benchmark/all")
async def benchmark_all() -> Dict:
    """Get benchmark comparison for all pilots"""
    pilots = list_pilots()
    benchmarks = []
    
    for pilot in pilots:
        bench = advanced_analytics.benchmark_pilot(pilot['id'])
        benchmarks.append(bench)
    
    # Summary statistics
    revenue_pcts = [b.get('benchmarks', {}).get('revenue', {}).get('percentile', 50) for b in benchmarks]
    roi_pcts = [b.get('benchmarks', {}).get('roi', {}).get('percentile', 50) for b in benchmarks]
    
    return {
        'total_pilots': len(pilots),
        'benchmarks': benchmarks,
        'summary': {
            'avg_revenue_percentile': round(sum(revenue_pcts) / len(revenue_pcts), 1) if revenue_pcts else 0,
            'avg_roi_percentile': round(sum(roi_pcts) / len(roi_pcts), 1) if roi_pcts else 0,
            'top_performers': [b for b in benchmarks if b.get('performance_summary') == 'Top Performer'],
            'needs_attention': [b for b in benchmarks if b.get('performance_summary') == 'Needs Attention']
        }
    }


@router.get("/trends/{pilot_id}")
async def get_trends(pilot_id: int) -> Dict:
    """Get trend analysis for a pilot"""
    forecast = advanced_analytics.forecast_roi(pilot_id, 90)
    churn = advanced_analytics.predict_churn_risk(pilot_id)
    benchmark = advanced_analytics.benchmark_pilot(pilot_id)
    
    return {
        'pilot_id': pilot_id,
        'forecast': forecast,
        'churn_risk': churn,
        'benchmark': benchmark,
        'insights': {
            'roi_trend': forecast.get('trend'),
            'churn_risk_level': churn.get('churn_risk_level'),
            'performance_vs_peers': benchmark.get('performance_summary'),
            'recommendations': [
                forecast.get('trend'),
                churn.get('recommendation'),
                f"Revenue: {benchmark.get('benchmarks', {}).get('revenue', {}).get('percentile')}th percentile"
            ]
        }
    }


@router.post("/insights/program")
async def get_program_insights() -> Dict:
    """Get comprehensive program-wide insights"""
    pilots = list_pilots()
    
    # Analyze all pilots
    forecasts = [advanced_analytics.forecast_roi(p['id'], 30) for p in pilots]
    churns = [advanced_analytics.predict_churn_risk(p['id']) for p in pilots]
    
    high_risk = [c for c in churns if c.get('churn_risk_level') == 'high']
    high_growth = [f for f in forecasts if f.get('trend') == 'increasing']
    
    return {
        'total_pilots': len(pilots),
        'high_churn_risk': len(high_risk),
        'high_growth_pilots': len(high_growth),
        'churn_rate_pct': round(len(high_risk) / len(pilots) * 100, 1) if pilots else 0,
        'growth_rate_pct': round(len(high_growth) / len(pilots) * 100, 1) if pilots else 0,
        'at_risk_pilots': high_risk[:5],
        'high_growth_pilots': high_growth[:5],
        'action_items': [
            f'{len(high_risk)} pilots at risk of churn',
            f'{len(high_growth)} pilots showing strong growth',
            'Review at-risk pilots for support opportunities',
            'Amplify successful strategies from high-growth pilots'
        ]
    }
