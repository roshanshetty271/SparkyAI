"""
Generate performance report from Langfuse data.

This script fetches production metrics from Langfuse and generates
a comprehensive performance report.

Usage:
    python scripts/performance_report.py --days 7 --output report.html
"""

import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

try:
    from langfuse import Langfuse
except ImportError:
    print("Please install langfuse: pip install langfuse")
    exit(1)

from agent_core.config import settings


def fetch_metrics(client: Langfuse, days: int) -> Dict[str, Any]:
    """
    Fetch performance metrics from Langfuse.
    
    Args:
        client: Langfuse client instance
        days: Number of days to analyze
        
    Returns:
        Dictionary of metrics
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch traces
    traces = client.get_traces(
        from_timestamp=start_date,
        to_timestamp=datetime.now()
    )
    
    # Calculate metrics
    total_requests = len(traces)
    total_latency = sum(t.latency for t in traces if t.latency)
    error_count = sum(1 for t in traces if t.level == "ERROR")
    
    # Latencies
    latencies = sorted([t.latency for t in traces if t.latency])
    p50 = latencies[len(latencies) // 2] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    
    # Fetch scores
    scores = client.get_scores(
        from_timestamp=start_date,
        to_timestamp=datetime.now()
    )
    
    quality_scores = [s.value for s in scores if s.name == "response_quality"]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
    
    # Fetch generations for cost
    generations = client.get_generations(
        from_timestamp=start_date,
        to_timestamp=datetime.now()
    )
    
    total_cost = sum(g.calculated_total_cost or 0 for g in generations)
    total_tokens = sum(g.usage.total_tokens or 0 for g in generations if g.usage)
    
    return {
        "period_days": days,
        "total_requests": total_requests,
        "success_rate": (total_requests - error_count) / total_requests * 100 if total_requests > 0 else 0,
        "error_count": error_count,
        "avg_latency_ms": total_latency / total_requests if total_requests > 0 else 0,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "p99_latency_ms": p99,
        "avg_quality_score": avg_quality,
        "quality_evaluations": len(quality_scores),
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "cost_per_request": total_cost / total_requests if total_requests > 0 else 0,
    }


def generate_html_report(metrics: Dict[str, Any], output_file: str):
    """Generate HTML report from metrics."""
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>SparkyAI Performance Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 1200px;
            margin: 40px auto;
            padding: 20px;
            background: #0a0a0a;
            color: #e0e0e0;
        }}
        h1 {{
            background: linear-gradient(135deg, #00d9ff 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #888;
            margin-bottom: 40px;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 12px;
            padding: 24px;
        }}
        .metric-label {{
            color: #888;
            font-size: 14px;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 36px;
            font-weight: bold;
            color: #00d9ff;
        }}
        .metric-unit {{
            font-size: 16px;
            color: #888;
            margin-left: 4px;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section-title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #fff;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: #1a1a1a;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{
            background: #222;
            color: #00d9ff;
            font-weight: 600;
        }}
        .status-good {{ color: #00ff9f; }}
        .status-warning {{ color: #ffaa00; }}
        .status-bad {{ color: #ff4444; }}
        .timestamp {{
            text-align: right;
            color: #666;
            font-size: 14px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <h1>SparkyAI Performance Report</h1>
    <div class="subtitle">Last {metrics['period_days']} days</div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-label">Total Requests</div>
            <div class="metric-value">{metrics['total_requests']:,}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Success Rate</div>
            <div class="metric-value class="{'status-good' if metrics['success_rate'] >= 99 else 'status-warning' if metrics['success_rate'] >= 95 else 'status-bad'}">{metrics['success_rate']:.1f}<span class="metric-unit">%</span></div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg Response Time</div>
            <div class="metric-value">{metrics['avg_latency_ms']:.0f}<span class="metric-unit">ms</span></div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Avg Quality Score</div>
            <div class="metric-value class="{'status-good' if metrics['avg_quality_score'] >= 0.85 else 'status-warning' if metrics['avg_quality_score'] >= 0.70 else 'status-bad'}">{metrics['avg_quality_score']:.2f}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Total Cost</div>
            <div class="metric-value">${metrics['total_cost_usd']:.2f}</div>
        </div>
        
        <div class="metric-card">
            <div class="metric-label">Cost per Request</div>
            <div class="metric-value">${metrics['cost_per_request']:.4f}</div>
        </div>
    </div>
    
    <div class="section">
        <div class="section-title">Response Time Percentiles</div>
        <table>
            <thead>
                <tr>
                    <th>Percentile</th>
                    <th>Latency (ms)</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>P50 (Median)</td>
                    <td>{metrics['p50_latency_ms']:.0f} ms</td>
                    <td class="{'status-good' if metrics['p50_latency_ms'] < 500 else 'status-warning' if metrics['p50_latency_ms'] < 1000 else 'status-bad'}">
                        {'✓ Good' if metrics['p50_latency_ms'] < 500 else '⚠ Slow' if metrics['p50_latency_ms'] < 1000 else '✗ Very Slow'}
                    </td>
                </tr>
                <tr>
                    <td>P95</td>
                    <td>{metrics['p95_latency_ms']:.0f} ms</td>
                    <td class="{'status-good' if metrics['p95_latency_ms'] < 2000 else 'status-warning' if metrics['p95_latency_ms'] < 5000 else 'status-bad'}">
                        {'✓ Good' if metrics['p95_latency_ms'] < 2000 else '⚠ Slow' if metrics['p95_latency_ms'] < 5000 else '✗ Very Slow'}
                    </td>
                </tr>
                <tr>
                    <td>P99</td>
                    <td>{metrics['p99_latency_ms']:.0f} ms</td>
                    <td class="{'status-good' if metrics['p99_latency_ms'] < 5000 else 'status-warning' if metrics['p99_latency_ms'] < 10000 else 'status-bad'}">
                        {'✓ Good' if metrics['p99_latency_ms'] < 5000 else '⚠ Slow' if metrics['p99_latency_ms'] < 10000 else '✗ Very Slow'}
                    </td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <div class="section-title">Quality Metrics</div>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Average Quality Score</td>
                    <td class="{'status-good' if metrics['avg_quality_score'] >= 0.85 else 'status-warning' if metrics['avg_quality_score'] >= 0.70 else 'status-bad'}">{metrics['avg_quality_score']:.3f}</td>
                </tr>
                <tr>
                    <td>Total Evaluations</td>
                    <td>{metrics['quality_evaluations']:,}</td>
                </tr>
                <tr>
                    <td>Evaluation Coverage</td>
                    <td>{(metrics['quality_evaluations'] / metrics['total_requests'] * 100) if metrics['total_requests'] > 0 else 0:.1f}%</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="section">
        <div class="section-title">Cost Analysis</div>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Total API Cost</td>
                    <td>${metrics['total_cost_usd']:.2f}</td>
                </tr>
                <tr>
                    <td>Total Tokens</td>
                    <td>{metrics['total_tokens']:,}</td>
                </tr>
                <tr>
                    <td>Cost per Request</td>
                    <td>${metrics['cost_per_request']:.4f}</td>
                </tr>
                <tr>
                    <td>Projected Monthly Cost</td>
                    <td>${(metrics['total_cost_usd'] / metrics['period_days'] * 30):.2f}</td>
                </tr>
            </tbody>
        </table>
    </div>
    
    <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
</body>
</html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✅ Report generated: {output_file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate SparkyAI performance report")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    parser.add_argument("--output", type=str, default="performance_report.html", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Also output JSON data")
    
    args = parser.parse_args()
    
    # Initialize Langfuse client
    if not settings.langfuse_enabled:
        print("❌ Langfuse not configured. Please set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return
    
    print(f"📊 Fetching metrics from Langfuse (last {args.days} days)...")
    
    client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host
    )
    
    # Fetch metrics
    metrics = fetch_metrics(client, args.days)
    
    # Generate HTML report
    generate_html_report(metrics, args.output)
    
    # Optionally output JSON
    if args.json:
        json_file = args.output.replace('.html', '.json')
        with open(json_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"✅ JSON data saved: {json_file}")
    
    # Print summary
    print(f"\n📈 Performance Summary:")
    print(f"   Total Requests: {metrics['total_requests']:,}")
    print(f"   Success Rate: {metrics['success_rate']:.1f}%")
    print(f"   Avg Response Time: {metrics['avg_latency_ms']:.0f}ms")
    print(f"   Avg Quality Score: {metrics['avg_quality_score']:.2f}")
    print(f"   Total Cost: ${metrics['total_cost_usd']:.2f}")


if __name__ == "__main__":
    main()
