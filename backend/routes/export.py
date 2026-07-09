"""
Export API endpoints for custom data exports.
Supports CSV and Excel formats with column selection.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from db.export_service import (
    get_pilot_export_data, 
    get_action_export_data,
    export_to_csv,
    export_to_excel,
    get_available_columns,
    PILOT_COLUMNS,
    ACTION_COLUMNS
)

router = APIRouter()


class ExportRequest(BaseModel):
    data_type: str  # 'pilots' or 'actions'
    format: str = 'csv'  # 'csv' or 'excel'
    columns: Optional[List[str]] = None  # Specific columns to include


@router.get('/columns/{data_type}')
async def get_export_columns(data_type: str):
    """Get available columns for export."""
    try:
        columns = get_available_columns(data_type)
        if not columns:
            raise HTTPException(status_code=400, detail=f"Unknown data type: {data_type}")
        
        return {
            'data_type': data_type,
            'columns': columns,
            'column_count': len(columns),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/pilots')
async def export_pilots(req: ExportRequest):
    """Export pilots data to CSV or Excel."""
    try:
        # Get pilot data
        data = get_pilot_export_data(req.columns)
        
        if not data:
            raise HTTPException(status_code=400, detail="No pilot data available")
        
        # Use specified columns or all
        columns = req.columns or list(PILOT_COLUMNS.keys())
        
        if req.format == 'excel':
            buffer = export_to_excel(data, columns, sheet_name='Pilots')
            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=pilots.xlsx"}
            )
        else:  # CSV
            buffer = export_to_csv(data, columns)
            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=pilots.csv"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/actions')
async def export_actions(req: ExportRequest):
    """Export actions data to CSV or Excel."""
    try:
        # Get action data
        data = get_action_export_data(req.columns)
        
        if not data:
            raise HTTPException(status_code=400, detail="No action data available")
        
        # Use specified columns or all
        columns = req.columns or list(ACTION_COLUMNS.keys())
        
        if req.format == 'excel':
            buffer = export_to_excel(data, columns, sheet_name='Actions')
            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=actions.xlsx"}
            )
        else:  # CSV
            buffer = export_to_csv(data, columns)
            return StreamingResponse(
                iter([buffer.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=actions.csv"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/pilots/csv')
async def export_pilots_csv(columns: Optional[str] = None):
    """Quick export pilots to CSV. Columns as comma-separated string."""
    try:
        col_list = columns.split(',') if columns else None
        data = get_pilot_export_data(col_list)
        
        if not data:
            raise HTTPException(status_code=400, detail="No pilot data available")
        
        columns_to_use = col_list or list(PILOT_COLUMNS.keys())
        buffer = export_to_csv(data, columns_to_use)
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=pilots.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/pilots/excel')
async def export_pilots_excel(columns: Optional[str] = None):
    """Quick export pilots to Excel. Columns as comma-separated string."""
    try:
        col_list = columns.split(',') if columns else None
        data = get_pilot_export_data(col_list)
        
        if not data:
            raise HTTPException(status_code=400, detail="No pilot data available")
        
        columns_to_use = col_list or list(PILOT_COLUMNS.keys())
        buffer = export_to_excel(data, columns_to_use, sheet_name='Pilots')
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=pilots.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/actions/csv')
async def export_actions_csv(columns: Optional[str] = None):
    """Quick export actions to CSV. Columns as comma-separated string."""
    try:
        col_list = columns.split(',') if columns else None
        data = get_action_export_data(col_list)
        
        if not data:
            raise HTTPException(status_code=400, detail="No action data available")
        
        columns_to_use = col_list or list(ACTION_COLUMNS.keys())
        buffer = export_to_csv(data, columns_to_use)
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=actions.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/actions/excel')
async def export_actions_excel(columns: Optional[str] = None):
    """Quick export actions to Excel. Columns as comma-separated string."""
    try:
        col_list = columns.split(',') if columns else None
        data = get_action_export_data(col_list)
        
        if not data:
            raise HTTPException(status_code=400, detail="No action data available")
        
        columns_to_use = col_list or list(ACTION_COLUMNS.keys())
        buffer = export_to_excel(data, columns_to_use, sheet_name='Actions')
        
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=actions.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
