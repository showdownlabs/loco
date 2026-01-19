# Terminal Input UX Improvements ✨

## Summary

Updated the terminal input experience to feel more like Claude Code with improved keyboard shortcuts and visual feedback.

## Changes

### 1. **Multi-line Input Support**
- **Enter** → Submit (default, intuitive for chat)
- **Alt+Enter** → Insert newline (for multi-line input)
- Pasting multi-line content now works seamlessly

### 2. **Visual Separators** 
Added horizontal lines above and below the input area for better visual clarity:
```
────────────────────────────────────
>  your message here
────────────────────────────────────
```

### 3. **Paste Detection**
Shows feedback when pasting multi-line content:
```
Pasted 5 lines
```

### 4. **Updated Welcome Message**
Now includes hint about Alt+Enter:
```
/help for commands · alt+enter for newline · ctrl+c to exit
```

## Technical Details

**File Modified**: `src/loco/ui/console.py`

- Added custom key bindings using `prompt_toolkit.key_binding.KeyBindings`
- Set `multiline=True` to support pasting, but Enter submits via custom bindings
- Added continuation prompt (`"  "`) for visual indentation on multi-line
- Separator lines use Rich's dim styling for subtle appearance

## Testing

```bash
# Test import
python -c "from loco.ui.console import Console; print('✓ OK')"

# Try it out
loco
# Then:
# - Type and press Enter → submits
# - Type and press Alt+Enter → adds newline
# - Paste multi-line text → shows "Pasted N lines"
```

## User Experience

Before: 
- ❌ No way to add newlines (Enter always submitted)
- ❌ No visual separation between input and output
- ❌ No feedback on paste operations

After:
- ✅ Enter submits (natural for chat interfaces)
- ✅ Alt+Enter adds newlines (power user feature)
- ✅ Clear visual boundaries around input
- ✅ Paste detection with feedback
- ✅ Feels like Claude Code! 🎉
