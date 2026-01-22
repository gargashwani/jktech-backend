"""User management commands"""

import logging
import sys

import click
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


@click.command(name="user:promote")
@click.argument("user_id", type=int)
@click.option("--superuser", is_flag=True, default=True, help="Promote user to superuser")
@click.option("--demote", is_flag=True, help="Demote user from superuser")
def promote_user(user_id: int, superuser: bool, demote: bool):
    """Promote or demote a user to/from superuser status"""
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Attempting to {'demote' if demote else 'promote'} user with ID {user_id}")
        
        # Validate user_id
        if user_id <= 0:
            error_msg = f"Invalid user ID: {user_id}. User ID must be a positive integer."
            logger.error(error_msg)
            click.echo(f"❌ {error_msg}")
            sys.exit(1)
        
        # Fetch user from database
        try:
            user = User.get(db, id=user_id)
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching user {user_id}: {str(e)}", exc_info=True)
            click.echo(f"❌ Database error occurred while fetching user. Please check your database connection.")
            sys.exit(1)
        
        if not user:
            error_msg = f"User with ID {user_id} not found."
            logger.warning(error_msg)
            click.echo(f"❌ {error_msg}")
            sys.exit(1)

        # Check current status
        current_status = user.is_superuser
        action = "demote" if demote else "promote"
        
        # Prevent unnecessary operations
        if demote and not current_status:
            logger.info(f"User {user.email} (ID: {user_id}) is already not a superuser.")
            click.echo(f"ℹ️  User {user.email} (ID: {user_id}) is already not a superuser.")
            return
        
        if not demote and current_status:
            logger.info(f"User {user.email} (ID: {user_id}) is already a superuser.")
            click.echo(f"ℹ️  User {user.email} (ID: {user_id}) is already a superuser.")
            return

        # Perform the operation
        try:
            user.is_superuser = False if demote else True
            db.commit()
            db.refresh(user)
            
            logger.info(
                f"Successfully {action}d user {user.email} (ID: {user_id}) "
                f"from superuser status: {current_status} to {user.is_superuser}"
            )
            
            if demote:
                click.echo(f"✅ User {user.email} (ID: {user_id}) has been demoted from superuser.")
            else:
                click.echo(f"✅ User {user.email} (ID: {user_id}) has been promoted to superuser.")
                click.echo(f"   They can now manage other users and access admin features.")
                
        except SQLAlchemyError as e:
            db.rollback()
            error_msg = f"Database error while updating user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            click.echo(f"❌ Failed to update user. Database error occurred.")
            click.echo(f"   Error details have been logged.")
            sys.exit(1)
        except Exception as e:
            db.rollback()
            error_msg = f"Unexpected error while updating user {user_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            click.echo(f"❌ An unexpected error occurred while updating user.")
            click.echo(f"   Error details have been logged.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        db.rollback()
        logger.warning("Operation cancelled by user (KeyboardInterrupt)")
        click.echo("\n⚠️  Operation cancelled.")
        sys.exit(130)
    except Exception as e:
        db.rollback()
        error_msg = f"Unexpected error in promote_user command: {str(e)}"
        logger.error(error_msg, exc_info=True)
        click.echo(f"❌ An unexpected error occurred.")
        click.echo(f"   Error details have been logged.")
        sys.exit(1)
    finally:
        try:
            db.close()
            logger.debug("Database session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing database session: {str(e)}")


@click.command(name="user:list")
@click.option("--superuser", is_flag=True, help="List only superusers")
@click.option("--limit", type=int, default=1000, help="Maximum number of users to list")
def list_users(superuser: bool, limit: int):
    """List all users or filter by superuser status"""
    db: Session = SessionLocal()
    
    try:
        logger.info(f"Listing users (superuser_only={superuser}, limit={limit})")
        
        # Validate limit
        if limit <= 0:
            error_msg = f"Invalid limit: {limit}. Limit must be a positive integer."
            logger.error(error_msg)
            click.echo(f"❌ {error_msg}")
            sys.exit(1)
        
        # Fetch users from database
        try:
            if superuser:
                users = db.query(User).filter(User.is_superuser == True).limit(limit).all()
                logger.info(f"Found {len(users)} superuser(s)")
                click.echo("Superusers:")
            else:
                users = User.get_multi(db, skip=0, limit=limit)
                logger.info(f"Found {len(users)} user(s)")
                click.echo("All users:")
        except SQLAlchemyError as e:
            error_msg = f"Database error while fetching users: {str(e)}"
            logger.error(error_msg, exc_info=True)
            click.echo(f"❌ Database error occurred while fetching users.")
            click.echo(f"   Please check your database connection.")
            sys.exit(1)
        except Exception as e:
            error_msg = f"Unexpected error while fetching users: {str(e)}"
            logger.error(error_msg, exc_info=True)
            click.echo(f"❌ An unexpected error occurred while fetching users.")
            click.echo(f"   Error details have been logged.")
            sys.exit(1)

        if not users:
            logger.info("No users found matching the criteria")
            click.echo("  No users found.")
            return

        # Display users in a formatted table
        try:
            click.echo(f"\n{'ID':<5} {'Email':<30} {'Full Name':<25} {'Superuser':<10} {'Active':<10}")
            click.echo("-" * 85)
            
            for user in users:
                try:
                    full_name = user.full_name or 'N/A'
                    # Truncate long names/emails to fit the table
                    if len(full_name) > 24:
                        full_name = full_name[:21] + "..."
                    email = user.email
                    if len(email) > 29:
                        email = email[:26] + "..."
                    
                    click.echo(
                        f"{user.id:<5} {email:<30} {full_name:<25} "
                        f"{'Yes' if user.is_superuser else 'No':<10} "
                        f"{'Yes' if user.is_active else 'No':<10}"
                    )
                except Exception as e:
                    logger.warning(f"Error displaying user {getattr(user, 'id', 'unknown')}: {str(e)}")
                    # Continue with next user
                    continue
            
            click.echo(f"\nTotal: {len(users)} user(s)")
            logger.info(f"Successfully displayed {len(users)} user(s)")
            
        except Exception as e:
            error_msg = f"Error while displaying users: {str(e)}"
            logger.error(error_msg, exc_info=True)
            click.echo(f"❌ Error occurred while displaying users.")
            click.echo(f"   Error details have been logged.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user (KeyboardInterrupt)")
        click.echo("\n⚠️  Operation cancelled.")
        sys.exit(130)
    except Exception as e:
        error_msg = f"Unexpected error in list_users command: {str(e)}"
        logger.error(error_msg, exc_info=True)
        click.echo(f"❌ An unexpected error occurred.")
        click.echo(f"   Error details have been logged.")
        sys.exit(1)
    finally:
        try:
            db.close()
            logger.debug("Database session closed successfully")
        except Exception as e:
            logger.warning(f"Error closing database session: {str(e)}")

