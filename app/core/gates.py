from app.models.user import User


class Gate:
    @staticmethod
    def before(user: User) -> bool:
        """
        Run before any gate check
        """
        return True

    @staticmethod
    def is_admin(user: User) -> bool:
        """
        Check if user is admin
        """
        return user.is_superuser

    @staticmethod
    def is_active(user: User) -> bool:
        """
        Check if user is active
        """
        return user.is_active

    @staticmethod
    def owns_resource(user: User, resource_user_id: int) -> bool:
        """
        Check if user owns the resource
        """
        return user.id == resource_user_id

    @staticmethod
    def can_manage_users(user: User) -> bool:
        """
        Check if user can manage other users
        """
        return user.is_superuser

    @staticmethod
    def can_view_users(user: User) -> bool:
        """
        Check if user can view other users
        """
        return user.is_superuser or user.is_active
