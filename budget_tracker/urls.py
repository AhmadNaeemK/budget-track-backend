from os import path

from django.contrib import admin
from django.urls import include, path

from django.conf import settings
from django.conf.urls.static import static

from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView)

import debug_toolbar

urlpatterns = [
    path('admin/', admin.site.urls),
    path('__debug__/', include(debug_toolbar.urls)),
    path('', include('wallet.urls')),
    path('user/', include('accounts.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
