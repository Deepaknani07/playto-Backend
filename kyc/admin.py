from django.contrib import admin

from kyc.models import AppUser, KYCSubmission, NotificationEvent

admin.site.register(AppUser)
admin.site.register(KYCSubmission)
admin.site.register(NotificationEvent)
