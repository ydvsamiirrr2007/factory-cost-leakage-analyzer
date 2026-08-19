import pandas as pd
import numpy as np

class CascadeEngine:
    """
    Implements the unique innovation: Cascade Loss Intelligence.
    Builds a dependency graph and computes total cascaded financial impact.
    """
    def __init__(self, df):
        self.df = df.copy()
        # Dependency rules: (cause_field, effect_field, propagation_coefficient)
        self.rules = [
            ('downtime_hrs', 'overtime_hours', 0.3),
            ('downtime_hrs', 'rejected_units', 0.2),
            ('rejected_units', 'rework_units', 0.8),
            ('rejected_units', 'material_waste', 0.4),
            ('overtime_hours', 'rejected_units', 0.1),
            ('downtime_hrs', 'maintenance_cost', 0.1)
        ]
        self.cascade_impacts = None

    def compute_cascade(self):
        results = []
        for idx, row in self.df.iterrows():
            direct_loss = row.get('total_leakage', 0)
            indirect_loss = 0
            for cause, effect, coef in self.rules:
                cause_val = row[cause]
                effect_val = row[effect]
                # Estimate effect cost (using average unit cost)
                if effect == 'overtime_hours':
                    effect_cost = effect_val * 300
                elif effect == 'rejected_units':
                    effect_cost = effect_val * 50
                elif effect == 'rework_units':
                    effect_cost = effect_val * 40
                elif effect == 'material_waste':
                    effect_cost = effect_val * 10
                elif effect == 'maintenance_cost':
                    effect_cost = effect_val
                else:
                    effect_cost = effect_val * 100
                # Avoid division by zero
                if effect_val > 0:
                    indirect_loss += cause_val * coef * (effect_cost / effect_val)
                else:
                    indirect_loss += cause_val * coef * 0  # no effect

            total_cascade = direct_loss + indirect_loss
            results.append({
                'production_id': idx,
                'machine_id': row['machine_id'],
                'product_id': row['product_id'],
                'shift': row['shift'],
                'direct_loss': direct_loss,
                'indirect_loss': indirect_loss,
                'total_cascade_loss': total_cascade,
                'downtime_reason': row['downtime_reason']
            })
        self.cascade_impacts = pd.DataFrame(results)
        return self.cascade_impacts

    def aggregate_cascade(self):
        if self.cascade_impacts is None:
            raise ValueError("Run compute_cascade() first.")
        agg = self.cascade_impacts.groupby('machine_id').agg({
            'direct_loss': 'sum',
            'indirect_loss': 'sum',
            'total_cascade_loss': 'sum'
        }).reset_index()
        agg['cascade_rank'] = agg['total_cascade_loss'].rank(ascending=False)
        return agg.sort_values('total_cascade_loss', ascending=False)