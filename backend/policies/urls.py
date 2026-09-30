from core.routers import OptionalSlashRouter

from .views import PolicyViewSet, ProductCategoryViewSet, ProductViewSet

router = OptionalSlashRouter()
router.register(r"policies", PolicyViewSet, basename="policy")
router.register(r"product-categories", ProductCategoryViewSet, basename="productcategory")
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = router.urls
