# Signup and workspace onboarding behavior — Brief

Goal: After signup, the user should connect Instagram first, then the app should auto-create the workspace and take the user to the main screen.

Flow
- User completes signup.
- Immediately show the Connect Instagram popup.
- The popup contains only a login button, not username or workspace name fields.
- After Instagram login succeeds, create the workspace automatically.
- After workspace creation, send the user to the main screen.

Workspace creation rules
- Do not ask for workspace name at signup or in the popup.
- Do not ask for Instagram username in the popup.
- Workspace name should be auto-generated.
- The newly created workspace should become the active workspace.

Settings behavior
- In Settings, clicking Add workspace should also open the Connect Instagram popup directly.
- The workspace should be created only after successful Instagram login.
- No manual workspace form should be shown in this flow.

UX intent
- Keep the connect step as the only required user action before workspace creation.
- Make the transition from connect -> auto-create -> main screen feel immediate and uninterrupted.
