from django.urls import path

from kyc import views

urlpatterns = [
    path("auth/signup", views.signup),
    path("merchant/submissions", views.MerchantSubmissionView.as_view()),
    path("merchant/submissions/<int:pk>", views.MerchantSubmissionDetailView.as_view()),
    path("merchant/submissions/<int:pk>/submit", views.merchant_submit),
    path("reviewer/queue", views.ReviewerQueueView.as_view()),
    path("reviewer/submissions/<int:pk>/transition", views.reviewer_transition),
    path("reviewer/metrics", views.reviewer_metrics),
]
