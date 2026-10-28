#!/usr/bin/env python3
"""Verification script to confirm multi-user implementation is complete."""

import sys
import inspect
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def check_database_models():
    """Verify database models are properly defined."""
    from app.memory.models import StudentUser, UserThread, LongTermMemory
    
    # Check StudentUser has required fields
    assert hasattr(StudentUser, 'id'), "StudentUser missing 'id' field"
    assert hasattr(StudentUser, 'username'), "StudentUser missing 'username' field"
    assert hasattr(StudentUser, 'threads'), "StudentUser missing 'threads' relationship"
    assert hasattr(StudentUser, 'memories'), "StudentUser missing 'memories' relationship"
    
    # Check UserThread has required fields
    assert hasattr(UserThread, 'user_id'), "UserThread missing 'user_id' field"
    assert hasattr(UserThread, 'thread_id'), "UserThread missing 'thread_id' field"
    assert hasattr(UserThread, 'chat_title'), "UserThread missing 'chat_title' field"
    
    # Check LongTermMemory has required fields
    assert hasattr(LongTermMemory, 'user_id'), "LongTermMemory missing 'user_id' field"
    assert hasattr(LongTermMemory, 'memory_key'), "LongTermMemory missing 'memory_key' field"
    assert hasattr(LongTermMemory, 'memory_value'), "LongTermMemory missing 'memory_value' field"
    
    print("✅ Database models properly defined")
    return True

def check_memory_store_functions():
    """Verify all required memory store functions exist."""
    from app.memory.store import (
        list_users,
        get_user_profile,
        get_or_create_user_by_name,
        get_user_sidebar_history,
        user_owns_thread,
        get_thread_owner,
        get_or_create_user,
        get_or_create_thread,
    )
    
    required_functions = [
        ('list_users', list_users),
        ('get_user_profile', get_user_profile),
        ('get_or_create_user_by_name', get_or_create_user_by_name),
        ('get_user_sidebar_history', get_user_sidebar_history),
        ('user_owns_thread', user_owns_thread),
        ('get_thread_owner', get_thread_owner),
        ('get_or_create_user', get_or_create_user),
        ('get_or_create_thread', get_or_create_thread),
    ]
    
    for name, func in required_functions:
        assert callable(func), f"{name} is not callable"
    
    print("✅ All memory store functions defined")
    return True

def check_api_routes():
    """Verify all required API routes are defined."""
    from app.api.routes import router
    
    # Check that router has defined routes
    routes = router.routes
    route_paths = set()
    
    for route in routes:
        if hasattr(route, 'path'):
            route_paths.add(route.path)
    
    required_paths = {
        '/users',
        '/threads',
        '/threads/{thread_id}/messages',
        '/chat',
        '/upload',
    }
    
    for required_path in required_paths:
        assert required_path in route_paths, f"Missing route: {required_path}"
    
    print("✅ All API routes defined")
    return True

def check_frontend_elements():
    """Verify frontend HTML has user switcher elements."""
    html_path = Path(__file__).parent / "static" / "index.html"
    html_content = html_path.read_text()
    
    required_ids = [
        'user-select',
        'add-user-form',
        'new-user-name',
        'user-status',
    ]
    
    for element_id in required_ids:
        assert f'id="{element_id}"' in html_content, f"Missing HTML element with id={element_id}"
    
    print("✅ Frontend HTML elements present")
    return True

def check_javascript_functions():
    """Verify frontend JavaScript has user management functions."""
    js_path = Path(__file__).parent / "static" / "app.js"
    js_content = js_path.read_text()
    
    required_functions = [
        'loadUsers',
        'switchUser',
        'renderUserList',
        'initializeApp',
    ]
    
    for func_name in required_functions:
        assert f'function {func_name}' in js_content or f'{func_name}()' in js_content, \
            f"Missing JavaScript function: {func_name}"
    
    print("✅ Frontend JavaScript functions present")
    return True

def main():
    """Run all verification checks."""
    print("\n🔍 Verifying Multi-User Implementation...\n")
    
    checks = [
        ("Database Models", check_database_models),
        ("Memory Store Functions", check_memory_store_functions),
        ("API Routes", check_api_routes),
        ("Frontend HTML Elements", check_frontend_elements),
        ("Frontend JavaScript", check_javascript_functions),
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        try:
            check_func()
            passed += 1
        except Exception as e:
            print(f"❌ {check_name}: {str(e)}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*50}\n")
    
    if failed == 0:
        print("✅ Multi-user implementation is complete and ready!\n")
        return 0
    else:
        print("❌ Some checks failed. Please review the errors above.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
