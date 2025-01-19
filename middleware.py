from django.contrib.sites.models import Site
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class DynamicSiteMiddleware:
    """Middleware to set SITE_ID dynamically based on request domain."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the domain from the request
        domain = request.get_host().split(':')[0]  # Exclude port if present

        # Get the site corresponding to the domain
        try:
            site = Site.objects.get(domain=domain)
            settings.SITE_ID = site.id
            logger.info(f'Current Site: {domain}: {site}')

        except Site.DoesNotExist:
            logger.warning(f'No site found for domain: {domain}')
            pass  # Handle missing site logic if needed
            # By doing nothing, we fall back to the default site id
        return self.get_response(request)
