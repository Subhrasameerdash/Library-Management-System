from rest_framework.routers import DefaultRouter

from .views import BookViewSet, FineViewSet, LoanViewSet, ReservationViewSet

router = DefaultRouter()
router.register(r"books", BookViewSet)
router.register(r"loans", LoanViewSet)
router.register(r"reservations", ReservationViewSet)
router.register(r"fines", FineViewSet)

urlpatterns = router.urls
