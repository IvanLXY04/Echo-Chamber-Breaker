# backend/app/ui/a2ui_catalog.py

# A2UI Catalog definition for the frontend renderer
# The agent will use these components to instruct the frontend on how to build the Scorecard UI

A2UI_CATALOG = {
    "version": "v0.9",
    "components": [
        "Column",          # Layout container
        "Row",             # Layout container
        "Text",            # Standard text
        "WarningCard",     # Custom component: A red-tinted card for fallacies
        "SuccessCard",     # Custom component: A green-tinted card for strong arguments
        "ProgressBar"      # Custom component: To show the Logic Score (1-10)
    ],
    "examples": [
        {
            "intent": "Render a scorecard showing a detected Straw Man fallacy and a logic score of 4/10",
            "a2ui_json": {
                "updateComponents": {
                    "surfaceId": "scorecard",
                    "components": [
                        {"id": "root", "component": "Column", "children": ["score", "fallacy"]},
                        {"id": "score", "component": "ProgressBar", "value": 4, "max": 10, "label": "Argument Strength"},
                        {"id": "fallacy", "component": "WarningCard", "title": "Straw Man Detected", "message": "You misrepresented the opponent's view..."}
                    ]
                }
            }
        }
    ]
}
