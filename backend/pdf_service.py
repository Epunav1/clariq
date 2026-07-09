"""
PDF report generation for pilot results.
Creates shareable PDF summaries with metrics and insights.
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def generate_pilot_report_pdf(pilot_data: dict) -> BytesIO:
    """
    Generate a PDF report for a pilot's performance.
    
    Args:
        pilot_data: Dict with keys:
            - pilot: {id, name, email, store_name, contacted_at, created_at}
            - metrics: {reorder_count, discount_count, promotion_count, query_count, 
                       days_active, total_revenue, reorder_velocity}
            - timeline: Optional list of daily action data
    
    Returns:
        BytesIO object containing PDF data
    """
    try:
        # Create PDF buffer
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Container for report elements
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4a5568'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#2d3748')
        )
        
        # Extract data
        pilot = pilot_data.get('pilot', {})
        metrics = pilot_data.get('metrics', {})
        
        # Title
        elements.append(Paragraph("CLARIQ PILOT RESULTS REPORT", title_style))
        elements.append(Spacer(1, 0.15*inch))
        
        # Pilot info section
        elements.append(Paragraph("Pilot Information", heading_style))
        
        pilot_info = [
            ['Pilot Name', pilot.get('name', 'N/A')],
            ['Store Name', pilot.get('store_name', 'N/A')],
            ['Email', pilot.get('email', 'N/A')],
            ['Program Start', pilot.get('contacted_at', 'N/A')[:10] if pilot.get('contacted_at') else 'N/A'],
            ['Report Generated', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')]
        ]
        
        info_table = Table(pilot_info, colWidths=[2*inch, 4.5*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#edf2f7')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Performance metrics section
        elements.append(Paragraph("Performance Metrics", heading_style))
        
        metrics_data = [
            ['Metric', 'Value', 'Status'],
            ['Reorders', f"{metrics.get('reorder_count', 0)}", 
             '✓ Strong' if metrics.get('reorder_count', 0) >= 3 else '○ Tracking'],
            ['Discounts Used', f"{metrics.get('discount_count', 0)}", 
             '✓ Active' if metrics.get('discount_count', 0) > 0 else '○ Unused'],
            ['Promotions Triggered', f"{metrics.get('promotion_count', 0)}", 
             '✓ Active' if metrics.get('promotion_count', 0) > 0 else '○ Unused'],
            ['Queries Asked', f"{metrics.get('query_count', 0)}", 
             '✓ Engaged' if metrics.get('query_count', 0) > 0 else '○ Not used'],
            ['Days Active', f"{metrics.get('days_active', 0)}", ''],
            ['Reorder Velocity', f"{metrics.get('reorder_velocity', 0)}/day", ''],
            ['Revenue Generated', f"${metrics.get('total_revenue', 0):.2f}", 
             '✓ Real' if metrics.get('total_revenue', 0) > 0 else '◊ Estimated']
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.2*inch, 1.8*inch, 1.8*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        elements.append(metrics_table)
        elements.append(Spacer(1, 0.25*inch))
        
        # Summary and recommendations
        elements.append(Paragraph("Summary & Next Steps", heading_style))
        
        summary_text = generate_pilot_summary(metrics)
        elements.append(Paragraph(summary_text, normal_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Footer
        elements.append(Spacer(1, 0.25*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#a0aec0'),
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "© 2026 CLARIQ. This pilot report is confidential and intended for authorized recipients only.",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)
        return pdf_buffer
    
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        raise


def generate_pilot_summary(metrics: dict) -> str:
    """Generate a text summary based on pilot metrics."""
    reorders = metrics.get('reorder_count', 0)
    revenue = metrics.get('total_revenue', 0)
    days = metrics.get('days_active', 0)
    discounts = metrics.get('discount_count', 0)
    queries = metrics.get('query_count', 0)
    
    summary_parts = []
    
    # Engagement level
    if reorders >= 5:
        summary_parts.append(f"<b>Excellent engagement:</b> {reorders} reorders in {days} days indicates strong pilot adoption.")
    elif reorders >= 2:
        summary_parts.append(f"<b>Good engagement:</b> {reorders} reorders in {days} days shows promise.")
    elif reorders >= 1:
        summary_parts.append(f"<b>Moderate engagement:</b> {reorders} reorder detected. More time or outreach may increase usage.")
    else:
        summary_parts.append(f"<b>Limited engagement:</b> No reorders yet. Consider additional pilot support or marketing.")
    
    # Revenue impact
    if revenue > 100:
        summary_parts.append(f"Strong revenue contribution of ${revenue:.2f}.")
    elif revenue > 0:
        summary_parts.append(f"Generated ${revenue:.2f} in measurable revenue.")
    
    # Feature usage
    features_used = []
    if discounts > 0:
        features_used.append("discount feature")
    if queries > 0:
        features_used.append("AI queries")
    
    if features_used:
        summary_parts.append(f"Pilot actively used {' and '.join(features_used)}.")
    
    # Recommendation
    if reorders >= 3:
        summary_parts.append("<b>Recommendation:</b> Qualified for full platform conversion.")
    elif reorders >= 1:
        summary_parts.append("<b>Recommendation:</b> Consider extended pilot or targeted support.")
    else:
        summary_parts.append("<b>Recommendation:</b> Assess barriers to adoption before extending.")
    
    return "<br/>".join(summary_parts)
