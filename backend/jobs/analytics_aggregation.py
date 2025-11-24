"""Analytics aggregation job for daily aggregates."""
from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models.analytics_event import AnalyticsEvent
from backend.models.analytics_aggregate import AnalyticsDailyAggregate


def aggregate_daily_analytics(aggregation_date: Optional[date] = None) -> dict:
    """
    Aggregate analytics events for a specific date into daily aggregates.
    
    Args:
        aggregation_date: Date to aggregate (defaults to yesterday UTC)
    
    Returns:
        Dictionary with aggregation summary
    """
    db = SessionLocal()
    try:
        # Default to yesterday if not provided
        if aggregation_date is None:
            aggregation_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Calculate date range (start and end of day in UTC)
        start_datetime = datetime.combine(aggregation_date, datetime.min.time())
        end_datetime = start_datetime + timedelta(days=1)
        
        # Query events for the day
        events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.created_at >= start_datetime,
            AnalyticsEvent.created_at < end_datetime
        ).all()
        
        # Group by user_id, domain_id, preview_id, event_type
        aggregates = {}
        
        for event in events:
            key = (
                event.user_id,
                event.domain_id,
                event.preview_id
            )
            
            if key not in aggregates:
                aggregates[key] = {
                    'user_id': event.user_id,
                    'domain_id': event.domain_id,
                    'preview_id': event.preview_id,
                    'impressions': 0,
                    'clicks': 0
                }
            
            if event.event_type == 'impression':
                aggregates[key]['impressions'] += 1
            elif event.event_type == 'click':
                aggregates[key]['clicks'] += 1
        
        # Insert or update aggregate records
        inserted_count = 0
        updated_count = 0
        
        for key, data in aggregates.items():
            # Check if aggregate already exists
            existing = db.query(AnalyticsDailyAggregate).filter(
                AnalyticsDailyAggregate.date == aggregation_date,
                AnalyticsDailyAggregate.user_id == data['user_id'],
                AnalyticsDailyAggregate.domain_id == data['domain_id'],
                AnalyticsDailyAggregate.preview_id == data['preview_id']
            ).first()
            
            if existing:
                # Update existing aggregate
                existing.impressions = data['impressions']
                existing.clicks = data['clicks']
                updated_count += 1
            else:
                # Create new aggregate
                aggregate = AnalyticsDailyAggregate(
                    date=aggregation_date,
                    user_id=data['user_id'],
                    domain_id=data['domain_id'],
                    preview_id=data['preview_id'],
                    impressions=data['impressions'],
                    clicks=data['clicks']
                )
                db.add(aggregate)
                inserted_count += 1
        
        db.commit()
        
        return {
            'date': aggregation_date.isoformat(),
            'events_processed': len(events),
            'aggregates_created': inserted_count,
            'aggregates_updated': updated_count,
            'total_aggregates': len(aggregates)
        }
    
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

