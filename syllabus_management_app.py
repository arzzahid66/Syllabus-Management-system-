import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# Configuration
API_BASE_URL = "https://api.nlpbusiness.site"  # Your FastAPI server base URL (without /docs)

# Page configuration
st.set_page_config(
    page_title="Syllabus Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chapter-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def login_user(email, password):
    """Login user and return token"""
    try:
        # Based on main.py, all endpoints are under /api prefix
        login_endpoint = f"{API_BASE_URL}/api/login"
        
        st.info(f"Trying login endpoint: {login_endpoint}")
        
        response = requests.post(
            login_endpoint,
            json={"email": email, "password": password},
            timeout=10
        )
        
        st.info(f"Response status: {response.status_code}")
        st.info(f"Response content: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("succeeded"):
                return data["data"]["token"], data["data"]["username"], data["data"]["user_role"]
            else:
                st.error(f"Login failed: {data.get('message', 'Unknown error')}")
        else:
            st.error(f"Login failed with status {response.status_code}")
            
        return None, None, None
        
    except Exception as e:
        st.error(f"Login error: {str(e)}")
        return None, None, None

def get_all_chapters(token):
    """Get all chapters from API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/all-chapters", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("succeeded"):
                return data["data"]
        return []
    except Exception as e:
        st.error(f"Error fetching chapters: {str(e)}")
        return []

def get_chapter_details(chapter_id, token):
    """Get specific chapter details"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_BASE_URL}/api/syllabus/{chapter_id}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data.get("succeeded"):
                return data["data"]
        return None
    except Exception as e:
        st.error(f"Error fetching chapter details: {str(e)}")
        return None

def update_chapter(chapter_id, chapter_data, token):
    """Update or create chapter"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.put(f"{API_BASE_URL}/api/syllabus/{chapter_id}", 
                              json=chapter_data, headers=headers)
        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("succeeded"):
                return True, data["message"]
        return False, "Update failed"
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    # Initialize session state
    if 'token' not in st.session_state:
        st.session_state.token = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

    # Header
    st.markdown('<h1 class="main-header">📚 Syllabus Management System</h1>', unsafe_allow_html=True)

    # Sidebar for navigation
    with st.sidebar:
        st.header("Navigation")
        if st.session_state.token:
            st.success(f"Logged in as: {st.session_state.username}")
            st.info(f"Role: {st.session_state.user_role}")
            
            if st.button("Logout"):
                st.session_state.token = None
                st.session_state.username = None
                st.session_state.user_role = None
                st.rerun()
        else:
            st.warning("Please login to continue")

    # Main content
    if not st.session_state.token:
        # Login section
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.header("🔐 Login")
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="Enter your email")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if email and password:
                    token, username, user_role = login_user(email, password)
                    if token:
                        st.session_state.token = token
                        st.session_state.username = username
                        st.session_state.user_role = user_role
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please try again.")
                else:
                    st.error("Please fill in all fields.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        # Main dashboard
        st.header("📖 Chapter Management")
        
        # Get all chapters
        chapters = get_all_chapters(st.session_state.token)
        
        if chapters:
            # Display chapters in a table
            st.subheader("📋 All Chapters")
            df = pd.DataFrame(chapters)
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(df, use_container_width=True)
            
            # Chapter selection for editing
            st.subheader("✏️ Edit Chapter")
            chapter_ids = [chapter['chapter_id'] for chapter in chapters]
            selected_chapter_id = st.selectbox(
                "Select Chapter to Edit",
                chapter_ids,
                format_func=lambda x: f"Chapter {x}: {next((c['chapter_title'] for c in chapters if c['chapter_id'] == x), '')}"
            )
            
            if selected_chapter_id:
                # Get chapter details
                chapter_details = get_chapter_details(selected_chapter_id, st.session_state.token)
                
                if chapter_details:
                    with st.form(f"edit_chapter_{selected_chapter_id}"):
                        st.write(f"**Editing Chapter {selected_chapter_id}**")
                        
                        col1, col2 = st.columns(2)
                        
                        # Chapter Title and Summary (Full Width)
                        chapter_title = st.text_input("📖 Chapter Title", value=chapter_details.get('chapter_title', ''), 
                                                    help="Enter the title of the chapter")
                        
                        st.markdown("---")
                        
                        # Summary Section
                        st.subheader("📝 Summary")
                        summary = st.text_area("Chapter Summary", value=chapter_details.get('summary', ''), 
                                             height=120, placeholder="Enter a comprehensive summary of the chapter...",
                                             help="Provide a clear and concise summary of the chapter content")
                        
                        st.markdown("---")
                        
                        # Chapter Text Section
                        st.subheader("📚 Chapter Content")
                        chapter_text = st.text_area("Full Chapter Text", value=chapter_details.get('chapter_text', ''), 
                                                  height=200, placeholder="Enter the complete chapter content...",
                                                  help="Include all the detailed content for this chapter")
                        
                        st.markdown("---")
                        
                        # Key Points Section (Two Columns)
                        st.subheader("🎯 Key Points")
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**🔑 Important Things**")
                            important_things = st.text_area(
                                "Important concepts, facts, or points (one per line)", 
                                value='\n'.join(chapter_details.get('important_things', [])),
                                height=120, placeholder="• Key concept 1\n• Key concept 2\n• Key concept 3",
                                help="List important things to remember, one per line"
                            )
                            
                            st.markdown("**💡 Key Learnings**")
                            key_learnings = st.text_area(
                                "Main learning objectives (one per line)", 
                                value='\n'.join(chapter_details.get('key_learnings', [])),
                                height=120, placeholder="• Learning objective 1\n• Learning objective 2\n• Learning objective 3",
                                help="List what students should learn from this chapter, one per line"
                            )
                        
                        with col2:
                            st.markdown("**🏃 Exercises & Activities**")
                            exercises_activities = st.text_area(
                                "Practical exercises and activities (one per line)", 
                                value='\n'.join(chapter_details.get('exercises_activities', [])),
                                height=120, placeholder="• Exercise 1\n• Exercise 2\n• Activity 1",
                                help="List exercises and activities for students, one per line"
                            )
                            
                            st.markdown("**💬 Inspirational Quotes**")
                            quotes = st.text_area(
                                "Motivational or relevant quotes (one per line)", 
                                value='\n'.join(chapter_details.get('quotes', [])),
                                height=120, placeholder="• \"Quote 1\"\n• \"Quote 2\"\n• \"Quote 3\"",
                                help="Add motivational quotes related to the chapter, one per line"
                            )
                        
                        # Convert text areas to lists
                        def text_to_list(text):
                            return [line.strip() for line in text.split('\n') if line.strip()]
                        
                        submit_edit = st.form_submit_button("Update Chapter")
                        
                        if submit_edit:
                            chapter_data = {
                                "chapter_title": chapter_title,
                                "summary": summary,
                                "important_things": text_to_list(important_things),
                                "key_learnings": text_to_list(key_learnings),
                                "exercises_activities": text_to_list(exercises_activities),
                                "quotes": text_to_list(quotes),
                                "chapter_text": chapter_text
                            }
                            
                            success, message = update_chapter(selected_chapter_id, chapter_data, st.session_state.token)
                            
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    st.error("Could not fetch chapter details")
        else:
            st.info("No chapters found. Please add some chapters first.")
            
            # Option to create new chapter
            st.subheader("➕ Create New Chapter")
            with st.form("create_chapter"):
                # Chapter ID and Title
                col1, col2 = st.columns(2)
                with col1:
                    new_chapter_id = st.number_input("📖 Chapter ID", min_value=1, step=1, 
                                                   help="Enter a unique chapter ID")
                with col2:
                    new_chapter_title = st.text_input("📚 Chapter Title", 
                                                     placeholder="Enter chapter title",
                                                     help="Enter the title of the chapter")
                
                st.markdown("---")
                
                # Summary Section
                st.subheader("📝 Summary")
                new_summary = st.text_area("Chapter Summary", height=120, 
                                         placeholder="Enter a comprehensive summary of the chapter...",
                                         help="Provide a clear and concise summary of the chapter content")
                
                st.markdown("---")
                
                # Chapter Text Section
                st.subheader("📖 Chapter Content")
                new_chapter_text = st.text_area("Full Chapter Text", height=200, 
                                              placeholder="Enter the complete chapter content...",
                                              help="Include all the detailed content for this chapter")
                
                st.markdown("---")
                
                # Key Points Section (Two Columns)
                st.subheader("🎯 Key Points")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔑 Important Things**")
                    new_important_things = st.text_area(
                        "Important concepts, facts, or points (one per line)", 
                        height=120, placeholder="• Key concept 1\n• Key concept 2\n• Key concept 3",
                        help="List important things to remember, one per line"
                    )
                    
                    st.markdown("**💡 Key Learnings**")
                    new_key_learnings = st.text_area(
                        "Main learning objectives (one per line)", 
                        height=120, placeholder="• Learning objective 1\n• Learning objective 2\n• Learning objective 3",
                        help="List what students should learn from this chapter, one per line"
                    )
                
                with col2:
                    st.markdown("**🏃 Exercises & Activities**")
                    new_exercises_activities = st.text_area(
                        "Practical exercises and activities (one per line)", 
                        height=120, placeholder="• Exercise 1\n• Exercise 2\n• Activity 1",
                        help="List exercises and activities for students, one per line"
                    )
                    
                    st.markdown("**💬 Inspirational Quotes**")
                    new_quotes = st.text_area(
                        "Motivational or relevant quotes (one per line)", 
                        height=120, placeholder="• \"Quote 1\"\n• \"Quote 2\"\n \"Quote 3\"",
                        help="Add motivational quotes related to the chapter, one per line"
                    )
                
                def text_to_list(text):
                    return [line.strip() for line in text.split('\n') if line.strip()]
                
                create_button = st.form_submit_button("Create Chapter")
                
                if create_button:
                    if new_chapter_id and new_chapter_title:
                        chapter_data = {
                            "chapter_title": new_chapter_title,
                            "summary": new_summary,
                            "important_things": text_to_list(new_important_things),
                            "key_learnings": text_to_list(new_key_learnings),
                            "exercises_activities": text_to_list(new_exercises_activities),
                            "quotes": text_to_list(new_quotes),
                            "chapter_text": new_chapter_text
                        }
                        
                        success, message = update_chapter(new_chapter_id, chapter_data, st.session_state.token)
                        
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please provide Chapter ID and Title")

if __name__ == "__main__":
    main()
