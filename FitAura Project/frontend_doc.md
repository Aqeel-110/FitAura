# 🎨 FitAura Frontend Documentation

## Design System

### Color Palette - Black & Gold Theme

```css
Primary Background:   #0a0a0a (Deep Black)
Secondary Background: #121212 (Dark Gray)
Card Background:      #1a1a1a (Lighter Black)
Hover Background:     #242424 (Hover State)

Primary Accent:       #d4af37 (Gold)
Secondary Accent:     #ffd700 (Bright Gold)
Accent Glow:          rgba(212, 175, 55, 0.2)

Text Primary:         #ffffff (White)
Text Secondary:       #b0b0b0 (Light Gray)
Text Muted:           #808080 (Muted Gray)
```

### Typography

- **Primary Font**: Inter (Modern, Clean)
- **Display Font**: Playfair Display (Elegant headings)
- **Font Sizes**: 
  - H1: 3.5rem (56px)
  - H2: 2.5rem (40px)
  - H3: 2rem (32px)
  - Body: 1rem (16px)

### Component Library

#### Buttons

```html
<!-- Primary Button (Gold Gradient) -->
<button class="btn btn-primary">
    <span>Button Text</span>
    <i class="fas fa-arrow-right"></i>
</button>

<!-- Secondary Button (Dark with Border) -->
<button class="btn btn-secondary">
    <span>Button Text</span>
</button>

<!-- Large Button -->
<button class="btn btn-primary btn-large">
    <span>Large Button</span>
</button>

<!-- Full Width Button -->
<button class="btn btn-primary btn-full">
    <span>Full Width</span>
</button>

<!-- Icon Button -->
<button class="btn-icon">
    <i class="fas fa-heart"></i>
</button>
```

#### Cards

```html
<div class="feature-card">
    <div class="feature-icon">
        <i class="fas fa-star"></i>
    </div>
    <h3 class="feature-title">Title</h3>
    <p class="feature-description">Description text</p>
</div>
```

#### Forms

```html
<div class="form-group">
    <label for="input" class="form-label">
        <i class="fas fa-user"></i>
        Label Text
    </label>
    <input 
        type="text" 
        id="input" 
        class="form-input" 
        placeholder="Placeholder"
    >
    <small class="form-hint">Helper text</small>
</div>
```

## Page Structure

### 1. Landing Page (index.html)

**Sections:**
- Hero Section with animated cards
- Features Grid (3 cards)
- Benefits Section with mockup
- CTA Section
- Footer

**Key Features:**
- Floating animation on hero cards
- Smooth scroll to sections
- Gradient text effects
- Responsive grid layouts

### 2. Authentication Pages (login.html, signup.html)

**Layout:**
- Split design (50/50)
- Left: Branding with features
- Right: Form with glassmorphism

**Features:**
- Password toggle visibility
- Real-time validation
- Loading states
- Animated background

### 3. Chatbot Interface (chatbot.html)

**Layout:**
- Sidebar (280px fixed)
- Main chat area (flex)
- Optional recommendations panel

**Components:**
- Message bubbles (bot/user)
- Quick option buttons
- Image gallery
- Typing indicator
- Character counter

### 4. Recommendations Page

Will display saved outfits in a grid with filters

### 5. Profile Page

User stats and saved recommendations history

## Animations

### Slide In (Flash Messages)
```css
@keyframes slideIn {
    from {
        transform: translateX(400px);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}
```

### Float (Hero Cards)
```css
@keyframes float {
    0%, 100% { transform: translateY(0px); }
    50% { transform: translateY(-20px); }
}
```

### Typing Indicator
```css
@keyframes typing {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-8px); }
}
```

## Interactive Elements

### Chat Message Flow

1. User types in textarea
2. Press Enter or click send button
3. User message appears (right side, gold gradient)
4. Typing indicator shows
5. Bot message appears (left side, dark card)
6. If multiple choice, quick options appear
7. After all questions, recommendations display with images

### Image Gallery

- Grid layout (auto-fit, min 200px)
- Hover zoom effect
- Click to open full-screen modal
- Modal closes on click anywhere

### Quick Options

- Horizontal flex wrap
- Pill-shaped buttons
- Hover lift effect
- Click fills input and sends

## JavaScript Functions

### Main.js Utilities

```javascript
// Show notification
OutfitAI.showNotification('Message', 'success');

// Format date
OutfitAI.formatDateTime(date);

// Loading state
OutfitAI.setLoadingState(button, true, 'Loading...');

// Auto-resize textarea
OutfitAI.autoResizeTextarea(textarea);

// Copy to clipboard
OutfitAI.copyToClipboard(text);
```

### Chatbot.js Functions

```javascript
// Display messages
displayUserMessage(text);
displayBotMessage(text, questionData);

// Process answer
processAnswer(answer);

// Generate recommendations
generateRecommendations();

// Save recommendation
saveRecommendation();

// Image modal
openImageModal(imagePath);
```

## Responsive Breakpoints

```css
Desktop:  > 1024px  (Default)
Tablet:   768px - 1024px
Mobile:   < 768px
```

### Mobile Adaptations

- Sidebar becomes overlay (slide-in)
- Single column layouts
- Smaller font sizes
- Stack buttons vertically
- Hide decorative elements

## Icon Library

**Font Awesome 6.4.0** (Free Icons)

Commonly used:
- `fa-sparkles` - Brand icon
- `fa-robot` - Bot avatar
- `fa-user` - User avatar
- `fa-comments` - Chat
- `fa-bookmark` - Save
- `fa-heart` - Favorite
- `fa-arrow-right` - CTA buttons
- `fa-check-circle` - Success
- `fa-exclamation-triangle` - Error

## Performance Optimizations

1. **CSS Variables** - Easy theming
2. **Debounce/Throttle** - Scroll events
3. **Lazy Loading** - Images
4. **Animation GPU** - transform & opacity
5. **Minimize Reflows** - Batch DOM updates

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support  
- Safari: ✅ Full support
- Mobile browsers: ✅ Full support

## Accessibility Features

- Semantic HTML5
- ARIA labels where needed
- Keyboard navigation
- Focus visible states
- Alt text for images
- Color contrast (WCAG AA)

## File Structure

```
static/
├── css/
│   ├── style.css       # Main styles + Landing page
│   ├── auth.css        # Login/Signup pages
│   └── chatbot.css     # Chat interface
│
├── js/
│   ├── main.js         # Global utilities
│   └── chatbot.js      # Chat logic
│
└── images/
    └── (generated images stored here)
```

## Customization Guide

### Change Color Theme

Edit CSS variables in `style.css`:

```css
:root {
    --primary-accent: #your-color;
    --secondary-accent: #your-color;
}
```

### Add New Page

1. Extend `base.html`
2. Include necessary CSS
3. Use existing components
4. Follow naming conventions

### Modify Animations

All animations use CSS keyframes. Adjust:
- Duration: `0.3s`, `0.5s`, etc.
- Timing: `ease`, `ease-in-out`, `linear`
- Delay: `animation-delay`

## Best Practices

1. **Always escape user input** - Use `escapeHtml()` function
2. **Show loading states** - User feedback is crucial
3. **Handle errors gracefully** - Display friendly messages
4. **Mobile-first thinking** - Test on small screens
5. **Accessibility matters** - Use semantic HTML

## Testing Checklist

- [ ] All buttons work
- [ ] Forms validate correctly
- [ ] Images load properly
- [ ] Animations smooth
- [ ] Mobile responsive
- [ ] Cross-browser tested
- [ ] Keyboard navigation
- [ ] Error handling

## Future Enhancements

- [ ] Dark/Light theme toggle
- [ ] More animation options
- [ ] Voice input for chat
- [ ] Image zoom/pan
- [ ] Export recommendations as PDF
- [ ] Share recommendations
- [ ] Multiple color themes

---

**Design Philosophy:**  
Professional, modern, minimal yet elegant. Black & gold for luxury feel, smooth animations for polish, clear typography for readability.