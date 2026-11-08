"""
Romanian Text Processing Application - Main Entry Point

This is the primary entry point for the application. 
"""


def main():
    """Application entry point function."""
    try:
        from src.app.startup_manager import initialize_application
        
        startup_manager = initialize_application("RomanianTextEditor")
        context = startup_manager.get_application_context()
        logger = context.get("logger")
        
        # Create and run the text processing application
        app = startup_manager.create_text_processing_app()
        if app:
            app.run(startup_context=context)

        else:
            error_msg = "Failed to create text processing application"
            if logger:
                logger.critical(error_msg)
            else:
                print(f"CRITICAL: {error_msg}")
            return 1
        
        if logger:
            logger.debug("Application shutdown complete")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
