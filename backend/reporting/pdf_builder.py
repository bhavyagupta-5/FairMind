from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.units import cm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PDFBuilder:

    def build(self, results: dict, explanation: dict = None, remediation: dict = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=24, spaceAfter=8,
            textColor=colors.HexColor('#1e293b')
        )
        h2_style = ParagraphStyle(
            'CustomH2', parent=styles['Heading2'],
            fontSize=14, spaceAfter=6, spaceBefore=12,
            textColor=colors.HexColor('#334155')
        )
        body_style = ParagraphStyle(
            'CustomBody', parent=styles['Normal'],
            fontSize=11, leading=16
        )

        severity_colors = {
            "HIGH": "#dc2626",
            "MEDIUM": "#d97706",
            "LOW": "#16a34a",
            "PASS": "#16a34a"
        }
        sev_color = severity_colors.get(results.get("severity", "HIGH"), "#dc2626")
        story = []

        # ── Cover ──────────────────────────────────────────────
        story.append(Spacer(1, 1.5*cm))
        story.append(Paragraph("FairLens Audit Report", title_style))
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"Dataset: <b>{results.get('dataset_name', 'Unknown')}</b>", body_style))
        story.append(Paragraph(f"Protected Attribute: <b>{results.get('protected_attribute', '')}</b>", body_style))
        story.append(Paragraph(f"Target Column: <b>{results.get('target_column', '')}</b>", body_style))
        story.append(Paragraph(f"Audit Date: {datetime.now().strftime('%B %d, %Y')}", body_style))
        story.append(Paragraph(f"Model Accuracy: <b>{results.get('model_accuracy', 0):.1%}</b>", body_style))
        story.append(Paragraph(
            f"Verdict: <font color='{sev_color}'><b>{results.get('verdict', 'FAIL')} — {results.get('severity', 'HIGH')} RISK</b></font>",
            body_style
        ))
        story.append(Spacer(1, 0.8*cm))

        # ── Executive Summary ──────────────────────────────────
        story.append(Paragraph("Executive Summary", h2_style))
        groups = results.get("groups", [])
        di = results.get("overall_metrics", {}).get("disparate_impact", {})
        om = results.get("overall_metrics", {})

        if di:
            worst_group = min(di, key=di.get)
            worst_val = di.get(worst_group, 0)
            best_group = max(di, key=di.get)
            best_val = di.get(best_group, 1)
            summary_text = (
                f"This audit examined the model's behaviour across {len(groups)} demographic groups "
                f"using '{results.get('protected_attribute', '')}' as the protected attribute. "
                f"The model achieves an accuracy of {results.get('model_accuracy', 0):.1%}. "
                f"However, <b>{worst_group}</b> received positive outcomes at only {worst_val:.1%} of the rate "
                f"of <b>{best_group}</b> ({best_val:.1%}), resulting in a disparate impact score of {worst_val:.2f}. "
                f"This {'fails' if results.get('verdict') == 'FAIL' else 'borderlines'} the EEOC 4/5ths rule "
                f"(minimum threshold: 0.80)."
            )
        else:
            summary_text = "Audit completed. See metrics below for details."

        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 0.5*cm))

        # ── Fairness Metrics Table ─────────────────────────────
        story.append(Paragraph("Fairness Metrics", h2_style))
        metrics_data = [
            ["Metric", "Value", "Threshold", "Status"],
            [
                "Demographic Parity Ratio",
                f"{om.get('demographic_parity_ratio', 0):.3f}",
                "≥ 0.80",
                "✓ PASS" if om.get("demographic_parity_ratio", 0) >= 0.8 else "✗ FAIL"
            ],
            [
                "Equalized Odds Gap",
                f"{om.get('equalized_odds_gap', 0):.3f}",
                "≤ 0.10",
                "✓ PASS" if om.get("equalized_odds_gap", 0) <= 0.1 else "✗ FAIL"
            ],
        ]
        metrics_table = Table(metrics_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ]))
        story.append(metrics_table)
        story.append(Spacer(1, 0.5*cm))

        # ── Group Outcomes Table ───────────────────────────────
        story.append(Paragraph("Outcomes by Demographic Group", h2_style))
        group_metrics = results.get("group_metrics", {})
        gm_data = [["Group", "Positive Rate", "True Pos. Rate", "False Pos. Rate", "Disparate Impact"]]
        for g in groups:
            m = group_metrics.get(g, {})
            di_val = di.get(g, 0)
            gm_data.append([
                g,
                f"{m.get('selection_rate', 0):.1%}",
                f"{m.get('tpr', 0):.1%}",
                f"{m.get('fpr', 0):.1%}",
                f"{di_val:.3f} {'✓' if di_val >= 0.8 else '✗'}",
            ])
        group_table = Table(gm_data, colWidths=[4*cm, 3*cm, 3*cm, 3.5*cm, 3.5*cm])
        group_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ]))
        story.append(group_table)
        story.append(Spacer(1, 0.5*cm))

        # ── SHAP Chart ─────────────────────────────────────────
        if explanation and explanation.get("group_shap"):
            story.append(Paragraph("Feature Influence Analysis (SHAP)", h2_style))
            shap_img = self._render_shap_chart(explanation)
            if shap_img:
                story.append(shap_img)
                story.append(Spacer(1, 0.3*cm))

            drivers = explanation.get("top_bias_drivers", [])
            if drivers:
                story.append(Paragraph("Top Bias Drivers:", h2_style))
                for d in drivers[:3]:
                    story.append(Paragraph(f"• {d.get('description', '')}", body_style))
            story.append(Spacer(1, 0.5*cm))

        # ── Remediation Section ────────────────────────────────
        if remediation:
            story.append(Paragraph("Remediation Applied", h2_style))
            story.append(Paragraph(
                f"Technique: <b>{remediation.get('technique', '').replace('_', ' ').title()}</b>",
                body_style
            ))
            story.append(Paragraph(remediation.get("improvement_summary", ""), body_style))
            story.append(Spacer(1, 0.3*cm))

            before = remediation.get("before", {})
            after = remediation.get("after", {})
            rem_data = [
                ["Metric", "Before", "After", "Change"],
                [
                    "Demographic Parity Ratio",
                    f"{before.get('demographic_parity_ratio', 0):.3f}",
                    f"{after.get('demographic_parity_ratio', 0):.3f}",
                    f"+{after.get('demographic_parity_ratio', 0) - before.get('demographic_parity_ratio', 0):.3f}"
                ],
                [
                    "Equalized Odds Gap",
                    f"{before.get('equalized_odds_gap', 0):.3f}",
                    f"{after.get('equalized_odds_gap', 0):.3f}",
                    f"{after.get('equalized_odds_gap', 0) - before.get('equalized_odds_gap', 0):.3f}"
                ],
            ]
            rem_table = Table(rem_data, colWidths=[6*cm, 3*cm, 3*cm, 3*cm])
            rem_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#334155')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ]))
            story.append(rem_table)
            story.append(Spacer(1, 0.5*cm))

        # ── Recommendations ────────────────────────────────────
        story.append(Paragraph("Recommendations", h2_style))
        recommendations = [
            "Apply the Reweighing technique during model training to reduce sample bias before deployment.",
            "Conduct regular quarterly bias audits as the model continues to learn from new data.",
            "Consult legal and ethics teams before deploying this model in high-stakes contexts.",
            "Consider removing or transforming proxy features that correlate with the protected attribute.",
            "Document this audit report and maintain it as part of your AI governance records.",
        ]
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", body_style))
        story.append(Spacer(1, 0.5*cm))

        # ── Methodology ────────────────────────────────────────
        story.append(Paragraph("Methodology", h2_style))
        story.append(Paragraph(
            "Bias metrics computed using Microsoft Fairlearn. "
            "Debiasing using IBM AIF360 and Fairlearn ThresholdOptimizer. "
            "Explainability via SHAP (Lundberg & Lee, 2017). "
            "Fairness standard: EEOC 4/5ths rule (disparate impact ≥ 0.80).",
            body_style
        ))

        doc.build(story)
        return buffer.getvalue()

    def _render_shap_chart(self, explanation) -> Image:
        try:
            group_shap = explanation.get("group_shap", {})
            features = explanation.get("features", [])[:8]
            group_list = list(group_shap.keys())[:2]

            fig, ax = plt.subplots(figsize=(8, 4))
            x = range(len(features))
            width = 0.35
            chart_colors = ['#3b82f6', '#ef4444']

            for i, group in enumerate(group_list):
                vals = [group_shap[group].get(f, 0) for f in features]
                ax.bar(
                    [xi + i * width for xi in x], vals,
                    width, label=group,
                    color=chart_colors[i], alpha=0.85
                )

            ax.set_xticks([xi + width / 2 for xi in x])
            ax.set_xticklabels(features, rotation=30, ha='right', fontsize=9)
            ax.set_ylabel("Mean |SHAP value|")
            ax.set_title("Feature Influence by Demographic Group")
            ax.legend()
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            plt.tight_layout()

            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='PNG', dpi=150, bbox_inches='tight')
            plt.close()
            img_buffer.seek(0)
            return Image(img_buffer, width=14*cm, height=7*cm)

        except Exception as e:
            logger.warning("SHAP chart render failed: %s", str(e))
            return None