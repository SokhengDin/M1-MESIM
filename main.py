"""
main.py
───────
Entry point for the MESIM desktop application.

Run with:
    python main.py
"""

from app import ProjectMESIMApp


def main():
    app = ProjectMESIMApp()
    app.mainloop()


if __name__ == "__main__":
    main()
