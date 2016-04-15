import endpoints
from google.appengine.ext import ndb
from protorpc import remote, message_types

from messages import UserResponse, CreateUserForm, UpdateUserForm, GetUserForm
from models import User

CREATE_USER_REQUEST = endpoints.ResourceContainer(CreateUserForm)
UPDATE_USER_REQUEST = endpoints.ResourceContainer(UpdateUserForm)
DELETE_USER_REQUEST = endpoints.ResourceContainer(GetUserForm)

user_api = endpoints.api(name='user', version='v1')


@user_api.api_class(resource_name='user')
class UserApi(remote.Service):
    """User APIs"""

    @endpoints.method(request_message=CREATE_USER_REQUEST,
                      response_message=UserResponse,
                      path='create_user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create user w/ unique username and email."""
        # check for empty user_name
        if not request.user_name:
            raise endpoints.BadRequestException('ERR_EMPTY_USERNAME')

        # check for empty email
        if not request.email:
            raise endpoints.BadRequestException('ERR_EMPTY_EMAIL')

        # check for unique username
        if User.query(User.user_name == request.user_name).get():
            raise endpoints.ConflictException('ERR_USERNAME_EXISTS: {}'.format(request.user_name))

        # check if user is already registered
        if User.query(User.email == request.email).get():
            raise endpoints.ConflictException('ERR_EMAIL_EXISTS: {}'.format(request.email))

        # create user
        user = User(key=ndb.Key(User, request.user_name),
                    user_name=request.user_name,
                    email=request.email,
                    display_name=request.display_name)
        user.put()

        return UserResponse(user_name=user.user_name, email=user.email, display_name=user.display_name)

    @endpoints.method(request_message=UPDATE_USER_REQUEST,
                      response_message=UserResponse,
                      path='update_user',
                      name='update_user',
                      http_method='POST')
    def update_user(self, request):
        """Update existing user"""
        user = self._get_user(request.current_user_name)

        for field in request.all_fields():
            # check if any field has been updated
            if getattr(request, field.name) and field.name is not 'current_user_name':
                setattr(user, field.name, getattr(request, field.name))

        user.put()

        return UserResponse(user_name=user.user_name, email=user.email, display_name=user.display_name)

    @endpoints.method(request_message=DELETE_USER_REQUEST,
                      response_message=message_types.VoidMessage,
                      path='delete_user',
                      name='delete_user',
                      http_method='POST')
    def delete_user(self, request):
        """Delete existing user"""
        user = self._get_user(request.user_name)

        # delete the entity
        user.key.delete()

        return message_types.VoidMessage()

    @staticmethod
    def _get_user(user_name):
        user = User.query(User.user_name == user_name).get()

        if not user:
            raise endpoints.NotFoundException('ERR_USER_NOT_FOUND')

        return user
