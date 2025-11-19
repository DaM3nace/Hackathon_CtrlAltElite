# Loading Animation Added to Ask Button

## Changes Made

Added an animated loading indicator to the "Ask" button to provide visual feedback when searching for answers.

### 1. CSS Animation (lines 147-166)

```css
.submit-btn:disabled {
    background: #90caf9;
    cursor: not-allowed;
}

.loading-dots {
    display: inline-block;
}

.loading-dots::after {
    content: '.';
    animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
    0%, 20% { content: '.'; }
    40% { content: '..'; }
    60% { content: '...'; }
    80%, 100% { content: ''; }
}
```

### 2. Button HTML Update (lines 296-298)

```html
<button type="submit" class="submit-btn" id="askBtn">
    <span id="btnText">Ask</span>
</button>
```

### 3. JavaScript Loading State (lines 365-374)

```javascript
form.addEventListener('submit', function(e) {
    // Disable button and show loading animation
    askBtn.disabled = true;
    btnText.innerHTML = 'Searching<span class="loading-dots"></span>';

    // Clear input after a short delay
    setTimeout(() => {
        document.querySelector('.question-input').value = '';
    }, 100);
});
```

## User Experience

### Before Click:
- Button shows: **"Ask"**
- Button is blue (#2196f3)
- Button is clickable

### After Click:
- Button shows: **"Searching..."** (with animated dots)
- Button turns light blue (#90caf9)
- Button is disabled (prevents double submission)
- Dots animate in a cycle: `.` → `..` → `...` → ` ` (repeats)

### After Response:
- Page reloads with the answer
- Button returns to normal "Ask" state

## Animation Details

- **Duration**: 1.5 seconds per cycle
- **Pattern**: One dot → Two dots → Three dots → No dots (repeat)
- **Smooth transition**: Uses CSS steps animation for clean appearance

## Files Modified

- `templates/chat.html` - Added CSS, updated button HTML, added JavaScript

## Testing

1. Open http://127.0.0.1:8000
2. Type a question
3. Click "Ask" button
4. Observe:
   - Button text changes to "Searching..."
   - Animated dots appear
   - Button becomes disabled
   - Page reloads with answer

The animation provides clear visual feedback that the system is processing the query!
