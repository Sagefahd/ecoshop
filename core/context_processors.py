from django.conf import settings


def site_settings(request):
    """Makes the WhatsApp support number available in every template."""
    number = getattr(settings, "WHATSAPP_SUPPORT_NUMBER", "")
    return {
        "WHATSAPP_SUPPORT_NUMBER": number,
        "WHATSAPP_SUPPORT_LINK": f"https://wa.me/{number}" if number else "",
    }
