"""
Report Generator Module
Generates performance reports and charts
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import logging
import config
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_metrics(trades_df):
    """Calculate performance metrics"""
    try:
        if trades_df.empty:
            return {}
        
        trades_df['entry_time'] = pd.to_datetime(trades_df['entry_time'], utc=True)
        trades_df['exit_time'] = pd.to_datetime(trades_df['exit_time'], utc=True)
        
        # Basic metrics
        total_trades = len(trades_df)
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        total_pnl = trades_df['pnl'].sum()
        
        # Daily P&L
        trades_df['date'] = trades_df['exit_time'].dt.date
        daily_pnl = trades_df.groupby('date')['pnl'].sum().reset_index()
        daily_pnl['date'] = pd.to_datetime(daily_pnl['date'])
        
        # Cumulative P&L
        daily_pnl = daily_pnl.sort_values('date')
        daily_pnl['cumulative_pnl'] = daily_pnl['pnl'].cumsum()
        
        # Drawdown
        daily_pnl['running_max'] = daily_pnl['cumulative_pnl'].cummax()
        daily_pnl['drawdown'] = daily_pnl['cumulative_pnl'] - daily_pnl['running_max']
        max_drawdown = daily_pnl['drawdown'].min()
        
        # Best/worst day
        best_day = daily_pnl.loc[daily_pnl['pnl'].idxmax()]
        worst_day = daily_pnl.loc[daily_pnl['pnl'].idxmin()]
        
        # Average daily signals (approximate)
        date_range = (daily_pnl['date'].max() - daily_pnl['date'].min()).days
        avg_daily_signals = (total_trades / date_range) if date_range > 0 else 0
        
        # Monthly breakdown
        trades_df['month'] = trades_df['exit_time'].dt.to_period('M')
        monthly_stats = trades_df.groupby('month', group_keys=False).agg({
            'pnl': ['sum', 'count'],
            'pips': 'mean'
        }).reset_index()
        monthly_stats.columns = ['month', 'total_pnl', 'trades', 'avg_pips']
        monthly_stats['win_rate'] = trades_df.groupby('month', group_keys=False).apply(
            lambda x: (x['pnl'] > 0).sum() / len(x) * 100
        ).values
        monthly_stats['month'] = monthly_stats['month'].astype(str)
        
        metrics = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'max_drawdown': max_drawdown,
            'best_day': best_day,
            'worst_day': worst_day,
            'avg_daily_signals': avg_daily_signals,
            'daily_pnl': daily_pnl,
            'monthly_stats': monthly_stats
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        raise


def create_charts(metrics, output_dir):
    """Create performance charts"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        daily_pnl = metrics['daily_pnl']
        
        # Cumulative P&L chart
        plt.figure(figsize=(12, 6))
        plt.plot(daily_pnl['date'], daily_pnl['cumulative_pnl'], linewidth=2)
        plt.title('Cumulative P&L Over Time - VWAP Strategy', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Cumulative P&L ($)', fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'cumulative_pnl_6months_vwap.png'), dpi=150)
        plt.close()
        
        # Daily P&L chart
        plt.figure(figsize=(12, 6))
        colors = ['green' if x > 0 else 'red' for x in daily_pnl['pnl']]
        plt.bar(daily_pnl['date'], daily_pnl['pnl'], color=colors, alpha=0.7)
        plt.title('Daily P&L - VWAP Strategy', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('P&L ($)', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        plt.gcf().autofmt_xdate()
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'daily_pnl_6months_vwap.png'), dpi=150)
        plt.close()
        
        logger.info("Charts created successfully")
        
    except Exception as e:
        logger.error(f"Error creating charts: {str(e)}")
        raise


def generate_html_report(metrics, output_file):
    """Generate HTML performance report"""
    try:
        monthly_stats = metrics['monthly_stats']
        
        # Create monthly breakdown HTML
        monthly_html = ""
        for _, row in monthly_stats.iterrows():
            monthly_html += f"""
            <tr>
                <td>{row['month']}</td>
                <td>{int(row['trades'])}</td>
                <td>{row['win_rate']:.2f}%</td>
                <td>${row['total_pnl']:.2f}</td>
                <td>{row['avg_pips']:.2f}</td>
            </tr>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Forex Backtest Performance Report - 6 Months</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-card h3 {{ margin: 0; font-size: 14px; opacity: 0.9; }}
        .metric-card .value {{ font-size: 32px; font-weight: bold; margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; font-weight: bold; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .positive {{ color: #4CAF50; font-weight: bold; }}
        .negative {{ color: #f44336; font-weight: bold; }}
        .chart {{ margin: 20px 0; text-align: center; }}
        .chart img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Forex Backtest Performance Report</h1>
        <p><strong>Strategy:</strong> VWAP Mean Reversion (Price below/above VWAP ± 1.5 SD bands)</p>
        <p><strong>Pair:</strong> EUR/USD | <strong>Timeframe:</strong> 15-minute</p>
        <p><strong>Period:</strong> June 2024 - December 2024 (7 months)</p>
        <p><strong>Parameters:</strong> Target +8 pips, Stop -6 pips, VWAP return exit, Spread 1.0 pip</p>
        
        <div class="metrics">
            <div class="metric-card">
                <h3>Total Trades</h3>
                <div class="value">{metrics['total_trades']}</div>
            </div>
            <div class="metric-card">
                <h3>Win Rate</h3>
                <div class="value">{metrics['win_rate']:.2f}%</div>
            </div>
            <div class="metric-card">
                <h3>Total P&L</h3>
                <div class="value {'positive' if metrics['total_pnl'] >= 0 else 'negative'}">${metrics['total_pnl']:.2f}</div>
            </div>
            <div class="metric-card">
                <h3>Max Drawdown</h3>
                <div class="value negative">${metrics['max_drawdown']:.2f}</div>
            </div>
            <div class="metric-card">
                <h3>Avg Signals/Day</h3>
                <div class="value">{metrics['avg_daily_signals']:.2f}</div>
            </div>
        </div>
        
        <h2>Performance Summary</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
            </tr>
            <tr>
                <td>Best Day</td>
                <td>{metrics['best_day']['date'].strftime('%Y-%m-%d')} (${metrics['best_day']['pnl']:.2f})</td>
            </tr>
            <tr>
                <td>Worst Day</td>
                <td>{metrics['worst_day']['date'].strftime('%Y-%m-%d')} (${metrics['worst_day']['pnl']:.2f})</td>
            </tr>
        </table>
        
        <h2>Monthly Performance Breakdown</h2>
        <table>
            <tr>
                <th>Month</th>
                <th>Trades</th>
                <th>Win Rate</th>
                <th>Total P&L</th>
                <th>Avg Pips</th>
            </tr>
            {monthly_html}
        </table>
        
        <h2>Charts</h2>
        <div class="chart">
            <h3>Cumulative P&L</h3>
            <img src="charts/cumulative_pnl_6months_vwap.png" alt="Cumulative P&L Chart">
        </div>
        <div class="chart">
            <h3>Daily P&L</h3>
            <img src="charts/daily_pnl_6months_vwap.png" alt="Daily P&L Chart">
        </div>
    </div>
</body>
</html>
        """
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {output_file}")
        
    except Exception as e:
        logger.error(f"Error generating HTML report: {str(e)}")
        raise


def main():
    """Main function to generate report"""
    try:
        logger.info("=" * 70)
        logger.info("REPORT GENERATOR")
        logger.info("=" * 70)
        
        # Load backtest results
        if not os.path.exists(config.BACKTEST_RESULTS_FILE):
            raise FileNotFoundError(f"Backtest results file not found: {config.BACKTEST_RESULTS_FILE}")
        
        logger.info(f"Loaded trades from {config.BACKTEST_RESULTS_FILE}...")
        trades_df = pd.read_csv(config.BACKTEST_RESULTS_FILE)
        
        logger.info(f"Loaded {len(trades_df)} trades from {config.BACKTEST_RESULTS_FILE}")
        logger.info("Calculating performance metrics...")
        
        # Calculate metrics
        metrics = calculate_metrics(trades_df)
        
        # Print summary
        logger.info("=" * 60)
        logger.info(f"Total Trades: {metrics['total_trades']}")
        logger.info(f"Win Rate: {metrics['win_rate']:.2f}%")
        logger.info(f"Total P&L: ${metrics['total_pnl']:.2f}")
        logger.info(f"Average Daily Signals: {metrics['avg_daily_signals']:.2f}")
        logger.info(f"Max Drawdown: ${metrics['max_drawdown']:.2f}")
        logger.info(f"Best Day: {metrics['best_day']['date'].strftime('%Y-%m-%d')} (${metrics['best_day']['pnl']:.2f})")
        logger.info(f"Worst Day: {metrics['worst_day']['date'].strftime('%Y-%m-%d')} (${metrics['worst_day']['pnl']:.2f})")
        logger.info("=" * 60)
        
        # Create charts
        logger.info("Creating charts...")
        create_charts(metrics, config.CHARTS_DIR)
        
        # Generate HTML report
        logger.info("Generating HTML report...")
        generate_html_report(metrics, config.PERFORMANCE_REPORT_FILE)
        
        logger.info("Report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        raise


if __name__ == "__main__":
    main()

