from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import auth, models
from ..database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/debug",
    tags=["debug"],
    responses={404: {"description": "Not found"}},
)

@router.get("/schema/blog_posts")
async def check_blog_posts_schema(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Debug endpoint to check the schema of the blog_posts table.
    """
    # Get a connection to execute raw SQL
    connection = db.connection()
    
    # For SQLite
    try:
        result = connection.execute("PRAGMA table_info(blog_posts)").fetchall()
        columns = [{"name": col[1], "type": col[2], "notnull": col[3], "default": col[4]} for col in result]
        return {"table": "blog_posts", "columns": columns}
    except Exception as e:
        logger.error(f"Error checking schema: {str(e)}")
        return {"error": str(e)}

@router.get("/post/{post_id}")
async def get_raw_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Debug endpoint to get the raw data of a blog post.
    """
    try:
        # Get the post using raw SQL to see exactly what's in the database
        connection = db.connection()
        result = connection.execute(f"SELECT * FROM blog_posts WHERE id = {post_id}").fetchone()
        
        if not result:
            return {"error": "Post not found"}
            
        # Convert to dict
        columns = connection.execute("PRAGMA table_info(blog_posts)").fetchall()
        column_names = [col[1] for col in columns]
        post_dict = {column_names[i]: value for i, value in enumerate(result)}
        
        return {"post": post_dict}
    except Exception as e:
        logger.error(f"Error getting raw post: {str(e)}")
        return {"error": str(e)}
