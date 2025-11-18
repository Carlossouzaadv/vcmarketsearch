"""
Visualization Module
Creates market maps and competitive matrices for visual analysis.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np


class MarketVisualizer:
    """Creates visual representations of market analysis."""

    def __init__(self):
        """Initialize the visualizer with default styling."""
        # Set modern style
        sns.set_style("whitegrid")
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 11
        plt.rcParams['axes.titlesize'] = 13
        plt.rcParams['figure.titlesize'] = 14

    def _extract_positioning_data(
        self,
        competitors: List[Dict],
        startup: Dict
    ) -> pd.DataFrame:
        """
        Extract positioning data from competitors.

        Args:
            competitors: List of competitor analyses
            startup: Target startup data

        Returns:
            DataFrame with positioning metrics
        """
        data = []

        # Score companies based on various factors
        for comp in competitors:
            if not comp.get('strengths'):
                continue

            name = comp.get('name', 'Unknown')

            # Calculate scores (simplified heuristic)
            feature_count = len(comp.get('key_features', []))
            strength_count = len(comp.get('strengths', []))
            weakness_count = len(comp.get('weaknesses', []))

            # Enterprise vs SMB (based on market position description)
            market_pos = comp.get('market_position', '').lower()
            is_enterprise = any(word in market_pos for word in ['enterprise', 'large', 'global'])
            is_smb = any(word in market_pos for word in ['smb', 'small', 'startup', 'self-serve'])

            target_score = 8 if is_enterprise else (3 if is_smb else 5.5)

            # Innovation vs Maturity (more features = more mature)
            innovation_score = max(1, 10 - (feature_count * 0.5))
            maturity_score = min(10, feature_count * 0.8)

            # Price positioning (heuristic from pricing model)
            pricing = comp.get('pricing_model', '').lower()
            is_premium = any(word in pricing for word in ['enterprise', 'custom', 'quote'])
            is_budget = any(word in pricing for word in ['free', 'low', 'affordable', 'starter'])

            price_score = 8 if is_premium else (3 if is_budget else 5.5)

            data.append({
                'name': name,
                'target_market': target_score,  # SMB (0) to Enterprise (10)
                'innovation': innovation_score,  # Mature (0) to Innovative (10)
                'price': price_score,  # Budget (0) to Premium (10)
                'feature_count': feature_count,
                'net_strength': strength_count - weakness_count,
                'is_target': False
            })

        # Add target startup
        if startup:
            target_features = len(startup.get('key_features', []))
            target_pos = startup.get('market_position', '').lower()
            is_enterprise = any(word in target_pos for word in ['enterprise', 'large'])
            is_smb = any(word in target_pos for word in ['smb', 'small', 'startup'])

            data.append({
                'name': startup.get('name', 'Target'),
                'target_market': 8 if is_enterprise else (3 if is_smb else 5.5),
                'innovation': max(1, 10 - (target_features * 0.5)),
                'price': 5.5,
                'feature_count': target_features,
                'net_strength': 0,
                'is_target': True
            })

        return pd.DataFrame(data)

    def create_market_map(
        self,
        competitors: List[Dict],
        startup: Dict,
        output_dir: str = "reports"
    ) -> str:
        """
        Create a market positioning map.

        Args:
            competitors: List of competitor analyses
            startup: Target startup information
            output_dir: Directory to save visualization

        Returns:
            Path to saved visualization
        """
        df = self._extract_positioning_data(competitors, startup)

        if df.empty:
            print("  ⚠ No data available for market map")
            return ""

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        fig.suptitle(f'Market Positioning Analysis: {startup.get("name", "Target Company")}',
                     fontsize=14, fontweight='bold')

        # Plot 1: Target Market vs Innovation
        for _, row in df.iterrows():
            color = '#FF6B6B' if row['is_target'] else '#4ECDC4'
            marker = 's' if row['is_target'] else 'o'
            size = 300 if row['is_target'] else 150

            ax1.scatter(row['target_market'], row['innovation'],
                       s=size, c=color, alpha=0.7, edgecolors='white',
                       linewidth=2, marker=marker, zorder=3 if row['is_target'] else 2)

            # Add labels
            ax1.annotate(row['name'],
                        (row['target_market'], row['innovation']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9, fontweight='bold' if row['is_target'] else 'normal',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='gray', alpha=0.8))

        ax1.set_xlabel('Target Market (SMB → Enterprise)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Market Approach (Mature → Innovative)', fontsize=11, fontweight='bold')
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 10)
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Market Positioning Map', fontsize=12, fontweight='bold', pad=10)

        # Add quadrant labels
        ax1.text(2.5, 8, 'Innovative\nSMB', ha='center', va='center',
                fontsize=9, color='gray', alpha=0.6)
        ax1.text(7.5, 8, 'Innovative\nEnterprise', ha='center', va='center',
                fontsize=9, color='gray', alpha=0.6)
        ax1.text(2.5, 2, 'Mature\nSMB', ha='center', va='center',
                fontsize=9, color='gray', alpha=0.6)
        ax1.text(7.5, 2, 'Mature\nEnterprise', ha='center', va='center',
                fontsize=9, color='gray', alpha=0.6)

        # Plot 2: Price vs Features
        for _, row in df.iterrows():
            color = '#FF6B6B' if row['is_target'] else '#95E1D3'
            marker = 's' if row['is_target'] else 'o'
            size = 300 if row['is_target'] else 150

            ax2.scatter(row['price'], row['feature_count'],
                       s=size, c=color, alpha=0.7, edgecolors='white',
                       linewidth=2, marker=marker, zorder=3 if row['is_target'] else 2)

            ax2.annotate(row['name'],
                        (row['price'], row['feature_count']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=9, fontweight='bold' if row['is_target'] else 'normal',
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                edgecolor='gray', alpha=0.8))

        ax2.set_xlabel('Pricing (Budget → Premium)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Feature Breadth', fontsize=11, fontweight='bold')
        ax2.set_xlim(0, 10)
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Price vs Feature Map', fontsize=12, fontweight='bold', pad=10)

        # Add legend
        target_patch = mpatches.Patch(color='#FF6B6B', label='Target Company')
        competitor_patch = mpatches.Patch(color='#4ECDC4', label='Competitors')
        fig.legend(handles=[target_patch, competitor_patch],
                  loc='lower center', ncol=2, frameon=True, fontsize=10)

        plt.tight_layout(rect=[0, 0.03, 1, 0.96])

        # Save
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"market_map_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"  ✓ Market map saved to {filepath}")
        return filepath

    def create_competitive_matrix(
        self,
        competitors: List[Dict],
        startup: Dict,
        output_dir: str = "reports"
    ) -> str:
        """
        Create competitive feature matrix.

        Args:
            competitors: List of competitor analyses
            startup: Target startup information
            output_dir: Directory to save visualization

        Returns:
            Path to saved visualization
        """
        # Extract all unique features
        all_features = set()
        for comp in competitors:
            for feature in comp.get('key_features', []):
                all_features.add(feature[:40])  # Truncate long features

        # Add target features
        for feature in startup.get('key_features', []):
            all_features.add(feature[:40])

        all_features = sorted(list(all_features))[:15]  # Limit to top 15

        if not all_features:
            print("  ⚠ No features available for matrix")
            return ""

        # Build matrix
        companies = []
        matrix_data = []

        # Add target
        companies.append(f"★ {startup.get('name', 'Target')}")
        target_features = [f[:40] for f in startup.get('key_features', [])]
        row = [1 if feat in target_features else 0 for feat in all_features]
        matrix_data.append(row)

        # Add competitors
        for comp in competitors[:12]:  # Limit to 12 competitors
            if not comp.get('key_features'):
                continue

            companies.append(comp.get('name', 'Unknown'))
            comp_features = [f[:40] for f in comp.get('key_features', [])]
            row = [1 if feat in comp_features else 0 for feat in all_features]
            matrix_data.append(row)

        if not matrix_data:
            print("  ⚠ No matrix data available")
            return ""

        # Create heatmap
        fig, ax = plt.subplots(figsize=(14, max(8, len(companies) * 0.5)))

        df = pd.DataFrame(matrix_data, index=companies, columns=all_features)

        sns.heatmap(df, annot=False, cmap=['#FFFFFF', '#4ECDC4'],
                   cbar=False, linewidths=1, linecolor='gray',
                   square=False, ax=ax)

        ax.set_title(f'Competitive Feature Matrix: {startup.get("name", "Target Company")}',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Features & Capabilities', fontsize=11, fontweight='bold')
        ax.set_ylabel('Companies', fontsize=11, fontweight='bold')

        # Rotate labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right', fontsize=9)
        plt.setp(ax.get_yticklabels(), rotation=0, fontsize=9)

        # Highlight target company
        ax.get_yticklabels()[0].set_weight('bold')
        ax.get_yticklabels()[0].set_color('#FF6B6B')

        plt.tight_layout()

        # Save
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"competitive_matrix_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)

        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()

        print(f"  ✓ Competitive matrix saved to {filepath}")
        return filepath

    def create_all_visualizations(
        self,
        competitors: List[Dict],
        startup: Dict,
        output_dir: str = "reports"
    ) -> Tuple[str, str]:
        """
        Create all visualizations.

        Args:
            competitors: List of competitor analyses
            startup: Target startup information
            output_dir: Directory to save visualizations

        Returns:
            Tuple of (market_map_path, competitive_matrix_path)
        """
        print("  → Creating visualizations")

        market_map_path = self.create_market_map(competitors, startup, output_dir)
        matrix_path = self.create_competitive_matrix(competitors, startup, output_dir)

        return market_map_path, matrix_path
