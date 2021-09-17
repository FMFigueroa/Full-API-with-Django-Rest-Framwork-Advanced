from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    # Serializador para el objeto de usuarios
    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}
    
    def create(self, validated_data):
        # Handle updating user account
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        #Actualizar al usario, confirma el password correctamente y lo retorna
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class AuthTokenSerializer(serializers.Serializer):
    # Serializador para el objeto de authentication del usuario
    email = serializers.CharField()
    password = serializers.CharField(style={'input_type':'password'},trim_whitespace=False)
    name = serializers.CharField()

    def validation(self, attrs):
        # Validar y Autenticar usuario
        email =  attrs.get('email')
        password = attrs.get('password')
        name = attrs.get('name')

        user = authenticate(
            request= self.context.get('request'),
            username = email,
            password = password,
            name = name
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials') 
            raise serializers.ValidationError(msg, code='authorization')
                
        attrs['user'] = user
        return attrs
