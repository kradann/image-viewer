BUTTON_STYLE = f"""
                color: #3cfb8b; 
                background-color: #303436;
            """
INFO_LABEL_STYLE = f"""
            font-size: 20px;
            color: #3cfb8b;
            padding: 10px;
            background: transparent;
        """
MENU_BAR_STYLE = f"""
            QMenuBar {{
                background-color: #181a1b;
                font-size: 18px;
                
            }}

            QMenuBar::item {{
                color: #3cfb8b;
                background-color: #181a1b;
            }}

            QMenuBar::item:selected {{
                background-color: #444444;
            }}

            QMenu {{
                background-color: #181a1b;
                color: #00ff00;
                font-size: 16px;
            }}

            QMenu::item:selected {{
                background-color: #444444;
            }}
        """

BATCH_INFO_STYLE = f"""
                    background: transparent; 
                    color: #3cfb8b; 
                    font-size: 20px;
                """

MAIN_WINDOW_STYLE = f"""
            QWidget#MainWindow {{
                background: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #6fcf9b,
                    stop:0.2 #4fa67a,
                    stop:0.4 #2e2e2e,
                    stop:1 #1a1a1a
                );
            }}
        """