from django import template

register = template.Library()


@register.filter
def status_class(value):
    return {
        "Running": "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300",
        "Working": "bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-300",
        "Waiting Client": "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-300",
        "Waiting Credentials": "bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-300",
        "Data Shared": "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/15 dark:text-cyan-300",
        "Delivered": "bg-cyan-100 text-cyan-700 dark:bg-cyan-500/15 dark:text-cyan-300",
        "Completed": "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300",
        "On Hold": "bg-slate-100 text-slate-700 dark:bg-slate-500/15 dark:text-slate-300",
        "Overdue": "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300",
        "Pending": "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-300",
        "Received": "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300",
    }.get(value, "bg-slate-100 text-slate-700 dark:bg-slate-500/15 dark:text-slate-300")


@register.filter
def priority_class(value):
    return {
        "High": "bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-300",
        "Medium": "bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-300",
        "Low": "bg-green-100 text-green-700 dark:bg-green-500/15 dark:text-green-300",
    }.get(value, "bg-slate-100 text-slate-700 dark:bg-slate-500/15 dark:text-slate-300")
