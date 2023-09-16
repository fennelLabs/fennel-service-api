from django.contrib.auth import get_user_model

import main


User = get_user_model()
APIGroup = main.models.APIGroup
APIGroupJoinRequest = main.models.APIGroupJoinRequest
UserKeys = main.models.UserKeys
Transaction = main.models.Transaction
