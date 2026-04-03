import logging
import os
import sys
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class QuotesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quotes'

    def ready(self):
        # Only auto-update when running the development server.
        # RUN_MAIN == 'true' means we are in the actual server process,
        # not in the auto-reloader watcher, so the thread starts exactly once.
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') == 'true':
            thread = threading.Thread(target=self._auto_update_data, daemon=True)
            thread.start()

    @staticmethod
    def _auto_update_data():
        import time
        time.sleep(3)  # Give Django a moment to finish starting up
        try:
            from quotes.models import FinancialObject, FinancialData
            from quotes.utils.date_helpers import prev_business_day
            from datetime import date

            last_stored = FinancialData.objects.order_by('-date').values_list('date', flat=True).first()
            expected = prev_business_day(date.today())

            if last_stored and last_stored >= expected:
                logger.info(f"[auto-update] Data already up to date (last: {last_stored}). Skipping refresh.")
                return

            fin_objs = FinancialObject.objects.all()
            logger.info(f"[auto-update] Starting data refresh for {fin_objs.count()} instruments (last stored: {last_stored})...")
            for fin_obj in fin_objs:
                fin_obj.update_nav_and_divs()
            logger.info("[auto-update] Data refresh complete.")
        except Exception:
            logger.exception("[auto-update] Data refresh failed.")