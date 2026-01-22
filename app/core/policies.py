from fastapi import HTTPException, status

from app.core.gates import Gate
from app.models.user import User




class Policy:
    @staticmethod
    def before(user: User, *args, **kwargs) -> bool:
        """
        Run before any policy check
        """
        return Gate.before(user)

    @staticmethod
    def view_any(user: User) -> bool:
        """
        Check if user can view any resource
        """
        if not Gate.before(user):
            return False
        return Gate.can_view_users(user)

    @staticmethod
    def view(user: User, resource_user_id: int) -> bool:
        """
        Check if user can view specific resource
        """
        if not Gate.before(user):
            return False
        return Gate.owns_resource(user, resource_user_id) or Gate.can_view_users(user)

    @staticmethod
    def create(user: User) -> bool:
        """
        Check if user can create resource
        """
        if not Gate.before(user):
            return False
        return Gate.is_active(user)

    @staticmethod
    def update(user: User, resource_user_id: int) -> bool:
        """
        Check if user can update resource
        """
        if not Gate.before(user):
            return False
        return Gate.owns_resource(user, resource_user_id) or Gate.can_manage_users(user)

    @staticmethod
    def delete(user: User, resource_user_id: int) -> bool:
        """
        Check if user can delete resource
        """
        if not Gate.before(user):
            return False
        # Check if user owns the resource or can manage users
        owns = Gate.owns_resource(user, resource_user_id)
        can_manage = Gate.can_manage_users(user)
        return owns or can_manage


class UserPolicy(Policy):
    @staticmethod
    def view_any(user: User) -> bool:
        if not Policy.view_any(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view users",
            )
        return True

    @staticmethod
    def view(user: User, resource_user_id: int) -> bool:
        if not Policy.view(user, resource_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user",
            )
        return True

    @staticmethod
    def update(user: User, resource_user_id: int) -> bool:
        if not Policy.update(user, resource_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user",
            )
        return True

    @staticmethod
    def delete(user: User, resource_user_id: int) -> bool:
        if not Policy.delete(user, resource_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user",
            )
        return True
