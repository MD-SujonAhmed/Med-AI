from rest_framework import serializers
from .models import Users

class SingUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = Users
        fields = ['email', 'full_name', 'password']
        
    def create(self, validated_data):
        user = Users.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password']
        )
        return user
        