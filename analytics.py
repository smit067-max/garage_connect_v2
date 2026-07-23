from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from bson import ObjectId

def _get_date_range(period):
    now = datetime.utcnow()
    if period == 'month':
        return now - relativedelta(months=1)
    elif period == '3months':
        return now - relativedelta(months=3)
    elif period == 'year':
        return now - relativedelta(years=1)
    elif period == '5years':
        return now - relativedelta(years=5)
    return datetime.min

def get_kpi_summary(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "status": "Completed",
            "completed_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": None,
            "total_revenue": {"$sum": "$total_price"},
            "total_parts_cost": {"$sum": "$parts_total"},
            "total_commission": {"$sum": "$commission_amount"},
            "jobs_completed": {"$sum": 1},
            "avg_job_value": {"$avg": "$total_price"},
            "unique_customers": {"$addToSet": "$customer_id"}
        }}
    ]
    result = list(db.bookings.aggregate(pipeline))
    if not result:
        return {
            "total_revenue": 0, "total_profit": 0, "jobs_completed": 0,
            "avg_job_value": 0, "repeat_customer_pct": 0, "avg_rating": 0,
            "rating_trend": 0
        }
        
    data = result[0]
    total_profit = data["total_revenue"] - data["total_parts_cost"] - data["total_commission"]
    repeat_customers = data["jobs_completed"] - len(data["unique_customers"])
    repeat_pct = (repeat_customers / data["jobs_completed"] * 100) if data["jobs_completed"] > 0 else 0
    
    # Rating
    garage = db.garages.find_one({"_id": ObjectId(garage_id)})
    
    return {
        "total_revenue": data["total_revenue"],
        "total_profit": total_profit,
        "jobs_completed": data["jobs_completed"],
        "avg_job_value": data["avg_job_value"],
        "repeat_customer_pct": repeat_pct,
        "avg_rating": garage.get("rating", 0),
        "rating_trend": 0  # Placeholder for trend
    }

def get_revenue_trend(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "status": "Completed",
            "completed_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": {
                "year": {"$year": "$completed_at"},
                "month": {"$month": "$completed_at"}
            },
            "revenue": {"$sum": "$total_price"},
            "parts": {"$sum": "$parts_total"},
            "comm": {"$sum": "$commission_amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]
    results = list(db.bookings.aggregate(pipeline))
    trend = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for r in results:
        profit = r["revenue"] - r["parts"] - r["comm"]
        month_name = f"{months[r['_id']['month']-1]} {r['_id']['year']}"
        trend.append({
            "month": month_name,
            "revenue": r["revenue"],
            "profit": profit
        })
    return trend

def get_service_breakdown(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "status": "Completed",
            "completed_at": {"$gte": start_date}
        }},
        {"$group": {
            "_id": "$service_type",
            "count": {"$sum": 1},
            "revenue": {"$sum": "$total_price"}
        }},
        {"$sort": {"revenue": -1}}
    ]
    results = list(db.bookings.aggregate(pipeline))
    return [{"service": r["_id"], "count": r["count"], "revenue": r["revenue"]} for r in results]

def get_monthly_comparison(db, garage_id):
    now = datetime.utcnow()
    this_month_start = datetime(now.year, now.month, 1)
    last_month_start = this_month_start - relativedelta(months=1)
    
    def get_stats(start, end):
        pipeline = [
            {"$match": {
                "garage_id": ObjectId(garage_id),
                "status": "Completed",
                "completed_at": {"$gte": start, "$lt": end}
            }},
            {"$group": {
                "_id": None,
                "jobs": {"$sum": 1},
                "revenue": {"$sum": "$total_price"},
                "parts": {"$sum": "$parts_total"},
                "comm": {"$sum": "$commission_amount"}
            }}
        ]
        res = list(db.bookings.aggregate(pipeline))
        if not res:
            return {"jobs": 0, "revenue": 0, "profit": 0}
        profit = res[0]["revenue"] - res[0]["parts"] - res[0]["comm"]
        return {"jobs": res[0]["jobs"], "revenue": res[0]["revenue"], "profit": profit}

    return {
        "this_month": get_stats(this_month_start, now),
        "last_month": get_stats(last_month_start, this_month_start)
    }

def get_customer_stats(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "status": "Completed",
            "completed_at": {"$gte": start_date}
        }},
        {"$sort": {"completed_at": 1}},
        {"$group": {
            "_id": "$customer_id",
            "first_visit": {"$first": "$completed_at"},
            "visits": {"$push": "$completed_at"}
        }}
    ]
    results = list(db.bookings.aggregate(pipeline))
    stats = {}
    for r in results:
        for visit in r["visits"]:
            month_key = f"{visit.year}-{visit.month:02d}"
            if month_key not in stats:
                stats[month_key] = {"new": 0, "returning": 0}
            if visit == r["first_visit"]:
                stats[month_key]["new"] += 1
            else:
                stats[month_key]["returning"] += 1
                
    formatted = [{"month": k, "new": v["new"], "returning": v["returning"]} for k, v in sorted(stats.items())]
    return formatted

def get_parts_usage(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "status": "Completed",
            "completed_at": {"$gte": start_date}
        }},
        {"$unwind": "$parts_used"},
        {"$group": {
            "_id": "$parts_used.name",
            "total_quantity_used": {"$sum": "$parts_used.quantity"},
            "total_value": {"$sum": "$parts_used.total"}
        }},
        {"$sort": {"total_quantity_used": -1}},
        {"$limit": 10}
    ]
    results = list(db.bookings.aggregate(pipeline))
    return [{"name": r["_id"], "total_quantity_used": r["total_quantity_used"], "total_value": r["total_value"]} for r in results]

def get_peak_days(db, garage_id, period):
    start_date = _get_date_range(period)
    pipeline = [
        {"$match": {
            "garage_id": ObjectId(garage_id),
            "created_at": {"$gte": start_date}
        }},
        {"$project": {
            "dayOfWeek": {"$dayOfWeek": "$created_at"}
        }},
        {"$group": {
            "_id": "$dayOfWeek",
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    results = list(db.bookings.aggregate(pipeline))
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    return [{"day": days[r["_id"]-1], "count": r["count"]} for r in results]
