
class DinnerGenieCard extends HTMLElement {
  setConfig(config) {
    this.config = {
      mode: 'week',
      max_days: 7,
      dashboard_path: '/dinner-genie',
      generate_button: 'button.dinner_genie_genereer_weekmenu',
      recipes_entity: 'sensor.dinner_genie_recepten',
      ...config,
    };
    this._selectedRecipe = this._selectedRecipe ?? null;
    this._search = this._search ?? '';
    this._dietFilter = this._dietFilter ?? 'all';
    this._categoryFilter = this._categoryFilter ?? 'all';
    this._lastRenderSignature = this._lastRenderSignature ?? '';
    this._dialogScrollTop = this._dialogScrollTop ?? 0;
    this._dialogTouchY = this._dialogTouchY ?? null;
    this._rendered = this._rendered ?? false;
  }

  set hass(hass) {
    this._hass = hass;
    const signature = this._renderSignature();
    if (!this._rendered || signature !== this._lastRenderSignature) {
      this.render();
    }
  }

  getCardSize() {
    return this.config?.mode === 'recipes' ? 6 : 4;
  }

  _state(entityId) {
    return this._hass?.states?.[entityId];
  }

  _dayEntity(day) {
    return this.config[`day_${day}_entity`] || `sensor.dinner_genie_dag_${day}`;
  }

  _replaceButton(day) {
    return this.config[`replace_day_${day}_button`] || `button.dinner_genie_vervang_dag_${day}`;
  }

  _callButton(entityId) {
    if (!entityId || !this._hass) return;
    this._hass.callService('button', 'press', { entity_id: entityId });
  }

  _renderSignature() {
    if (!this.config || !this._hass) return '';
    const mode = this.config.mode || 'week';
    if (mode === 'recipes') {
      const state = this._state(this.config.recipes_entity);
      return JSON.stringify({
        mode,
        title: this.config.title || '',
        recipes_entity: this.config.recipes_entity,
        state: state?.state || '',
        recipes: state?.attributes?.recipes || [],
      });
    }

    const maxDays = Number(this.config.max_days || 7);
    const days = [];
    for (let day = 1; day <= maxDays; day += 1) {
      const entityId = this._dayEntity(day);
      const state = this._state(entityId);
      days.push({
        entity_id: entityId,
        state: state?.state || '',
        attributes: state?.attributes || {},
      });
    }
    return JSON.stringify({
      mode,
      title: this.config.title || '',
      max_days: maxDays,
      days,
    });
  }

  _recipeFromEntity(entityId) {
    const state = this._state(entityId);
    if (!state) return null;
    return { state: state.state, entity_id: entityId, ...(state.attributes || {}) };
  }

  _allRecipes() {
    const state = this._state(this.config.recipes_entity);
    const recipes = state?.attributes?.recipes;
    return Array.isArray(recipes) ? recipes : [];
  }

  _escape(value) {
    return String(value ?? '').replace(/[&<>'"]/g, (char) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[char]));
  }

  _dietIcon(diet) {
    if (diet === 'vegan') return '🌿';
    if (diet === 'vegetarian') return '🌱';
    return '🍽️';
  }

  _image(recipe) {
    return recipe?.display_image || recipe?.image_url || '/api/dinner_genie/assets/placeholder_recipe.png';
  }

  _recipeTitle(recipe) {
    return recipe?.name || recipe?.state || 'Geen gerecht';
  }

  _ingredientsHtml(recipe) {
    const ingredients = recipe?.ingredients_formatted;
    if (Array.isArray(ingredients) && ingredients.length) {
      return `<ul>${ingredients.map((line) => `<li>${this._escape(line)}</li>`).join('')}</ul>`;
    }
    const markdown = recipe?.ingredients_markdown;
    if (markdown) {
      const lines = String(markdown).split('\n').map((line) => line.replace(/^[-*]\s*/, '')).filter(Boolean);
      return `<ul>${lines.map((line) => `<li>${this._escape(line)}</li>`).join('')}</ul>`;
    }
    return '<p class="muted">Geen ingrediënten beschikbaar.</p>';
  }

  _instructionsHtml(recipe) {
    const instructions = recipe?.instructions;
    if (!instructions) return '<p class="muted">Geen bereiding beschikbaar.</p>';
    const parts = String(instructions).split(/\n+/).filter(Boolean);
    if (parts.length > 1) {
      return parts.map((part) => `<p>${this._escape(part)}</p>`).join('');
    }
    return `<p>${this._escape(instructions)}</p>`;
  }

  _openRecipe(recipe) {
    this._selectedRecipe = recipe;
    this._dialogScrollTop = 0;
    this.render();
  }

  _closeRecipe() {
    this._selectedRecipe = null;
    this._dialogScrollTop = 0;
    this.render();
  }

  _renderMealCard(recipe, day, color) {
    const title = this._escape(this._recipeTitle(recipe));
    const prep = this._escape(recipe?.prep_time || '');
    const diet = this._escape(recipe?.diet_type || 'geen dieet');
    const category = this._escape(recipe?.category || '');
    return `
      <article class="dg-card" style="--accent:${color}">
        <div class="dg-card-header">
          <strong>${day ? `Dag ${day}` : 'Recept'}</strong>
          ${day ? `<button class="icon-button" data-action="replace" data-day="${day}" title="Vervang dag ${day}">↻</button>` : ''}
        </div>
        <img src="${this._escape(this._image(recipe))}" alt="" class="recipe-image" loading="lazy">
        <div class="dg-card-body">
          <h3>${title}</h3>
          <div class="meta">⏱ ${prep} <span>${this._dietIcon(recipe?.diet_type)} ${diet}</span></div>
          ${category ? `<div class="meta">🏷️ ${category}</div>` : ''}
          <button class="detail-button" data-action="details" data-entity="${this._escape(recipe?.entity_id || '')}" data-recipe-id="${this._escape(recipe?.recipe_id || recipe?.id || '')}">Details bekijken</button>
        </div>
      </article>
    `;
  }

  _renderWeek() {
    const colors = ['#F28C28', '#5BAE5B', '#4A90E2', '#8E6CCF', '#D96C6C', '#46B8B8', '#D9B44A'];
    const maxDays = Number(this.config.max_days || 7);
    const cards = [];
    for (let day = 1; day <= maxDays; day += 1) {
      const recipe = this._recipeFromEntity(this._dayEntity(day));
      cards.push(this._renderMealCard(recipe, day, colors[day - 1] || '#F28C28'));
    }
    return `
      <ha-card>
        <div class="header-row">
          <div>
            <h2>${this._escape(this.config.title || '🍽️ Weekmenu')}</h2>
            <p class="muted">Klik op details om het recept te bekijken of vervang één dag met ↻.</p>
          </div>
          <button class="header-action" data-action="generate">↻ Vernieuwen</button>
        </div>
        <div class="grid week-grid">${cards.join('')}</div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  _filteredRecipes() {
    const query = this._search.toLowerCase().trim();
    return this._allRecipes().filter((recipe) => {
      const haystack = [recipe.name, recipe.description, recipe.category, recipe.diet_type, recipe.recipe_type]
        .filter(Boolean).join(' ').toLowerCase();
      if (query && !haystack.includes(query)) return false;
      if (this._dietFilter !== 'all' && recipe.diet_type !== this._dietFilter) return false;
      if (this._categoryFilter !== 'all' && recipe.category !== this._categoryFilter) return false;
      return true;
    });
  }

  _categories() {
    const set = new Set();
    this._allRecipes().forEach((recipe) => {
      if (recipe.category) set.add(recipe.category);
    });
    return [...set].sort((a, b) => a.localeCompare(b));
  }

  _renderRecipes() {
    const recipes = this._filteredRecipes();
    const categories = this._categories();
    return `
      <ha-card>
        <div class="header-row">
          <div>
            <h2>${this._escape(this.config.title || '📖 Recepten')}</h2>
            <p class="muted" data-role="recipe-count">${recipes.length} van ${this._allRecipes().length} recepten</p>
          </div>
        </div>
        <div class="filters">
          <input id="search" type="search" placeholder="Zoeken..." value="${this._escape(this._search)}">
          <select id="diet">
            <option value="all" ${this._dietFilter === 'all' ? 'selected' : ''}>Alle diëten</option>
            <option value="vegetarian" ${this._dietFilter === 'vegetarian' ? 'selected' : ''}>Vegetarisch</option>
            <option value="vegan" ${this._dietFilter === 'vegan' ? 'selected' : ''}>Vegan</option>
          </select>
          <select id="category">
            <option value="all" ${this._categoryFilter === 'all' ? 'selected' : ''}>Alle categorieën</option>
            ${categories.map((category) => `<option value="${this._escape(category)}" ${this._categoryFilter === category ? 'selected' : ''}>${this._escape(category)}</option>`).join('')}
          </select>
        </div>
        <div class="grid recipes-grid" data-role="recipe-grid">
          ${recipes.map((recipe) => this._renderMealCard(recipe, null, '#F28C28')).join('') || '<p class="empty">Geen recepten gevonden.</p>'}
        </div>
      </ha-card>
      ${this._renderDialog()}
    `;
  }

  _renderDialog() {
    const recipe = this._selectedRecipe;
    if (!recipe) return '';
    return `
      <div class="dialog-backdrop" data-action="close">
        <div class="dialog" role="dialog" aria-modal="true">
          <button class="close" data-action="close">×</button>
          <img src="${this._escape(this._image(recipe))}" alt="" class="dialog-image">
          <h2>${this._escape(this._recipeTitle(recipe))}</h2>
          <div class="dialog-meta">⏱ ${this._escape(recipe.prep_time || '')} &nbsp; ${this._dietIcon(recipe.diet_type)} ${this._escape(recipe.diet_type || 'geen dieet')} ${recipe.category ? `&nbsp; 🏷️ ${this._escape(recipe.category)}` : ''}</div>
          ${recipe.description ? `<p class="description">${this._escape(recipe.description)}</p>` : ''}
          <h3>Ingrediënten</h3>
          ${this._ingredientsHtml(recipe)}
          <h3>Bereiding</h3>
          ${this._instructionsHtml(recipe)}
        </div>
      </div>
    `;
  }

  render() {
    if (!this.config || !this._hass) return;
    const activeElement = this.contains(document.activeElement) ? document.activeElement : null;
    const activeId = activeElement?.id || '';
    const selectionStart = activeElement && 'selectionStart' in activeElement ? activeElement.selectionStart : null;
    const selectionEnd = activeElement && 'selectionEnd' in activeElement ? activeElement.selectionEnd : null;
    const dialogScrollTop = this.querySelector('.dialog')?.scrollTop ?? this._dialogScrollTop;
    const mode = this.config.mode || 'week';
    this.innerHTML = `
      <style>${this._styles()}</style>
      ${mode === 'recipes' ? this._renderRecipes() : this._renderWeek()}
    `;
    this._bindEvents();
    this._restoreRenderState(activeId, selectionStart, selectionEnd, dialogScrollTop);
    this._lastRenderSignature = this._renderSignature();
    this._rendered = true;
  }

  _restoreRenderState(activeId, selectionStart, selectionEnd, dialogScrollTop) {
    const dialog = this.querySelector('.dialog');
    if (dialog) {
      this._dialogScrollTop = dialogScrollTop;
      dialog.scrollTop = dialogScrollTop;
    }

    if (!activeId) return;
    const activeElement = this.querySelector(`#${activeId}`);
    if (!activeElement) return;

    activeElement.focus({ preventScroll: true });
    if (selectionStart !== null && selectionEnd !== null && 'setSelectionRange' in activeElement) {
      activeElement.setSelectionRange(selectionStart, selectionEnd);
    }

    requestAnimationFrame(() => {
      const refreshedElement = this.querySelector(`#${activeId}`);
      if (!refreshedElement) return;
      refreshedElement.focus({ preventScroll: true });
      if (selectionStart !== null && selectionEnd !== null && 'setSelectionRange' in refreshedElement) {
        refreshedElement.setSelectionRange(selectionStart, selectionEnd);
      }
    });
  }

  _renderRecipeResults() {
    const recipes = this._filteredRecipes();
    const count = this.querySelector('[data-role="recipe-count"]');
    if (count) count.textContent = `${recipes.length} van ${this._allRecipes().length} recepten`;

    const grid = this.querySelector('[data-role="recipe-grid"]');
    if (!grid) return;
    grid.innerHTML = recipes.map((recipe) => this._renderMealCard(recipe, null, '#F28C28')).join('') || '<p class="empty">Geen recepten gevonden.</p>';
    this._bindDetailButtons(grid);
  }

  _bindDetailButtons(root = this) {
    root.querySelectorAll('[data-action="details"]').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        const entityId = button.getAttribute('data-entity');
        const recipeId = button.getAttribute('data-recipe-id');
        const recipe = entityId ? this._recipeFromEntity(entityId) : this._allRecipes().find((item) => String(item.recipe_id || item.id) === recipeId);
        this._openRecipe(recipe);
      });
    });
  }

  _stopInteractiveEvent(event) {
    event.stopPropagation();
  }

  _bindFilterControl(control, eventName, handler) {
    if (!control) return;
    ['click', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'focus', 'blur', 'keydown', 'keyup', 'compositionstart', 'compositionupdate', 'compositionend'].forEach((eventType) => {
      control.addEventListener(eventType, (event) => this._stopInteractiveEvent(event), { capture: true });
    });
    control.addEventListener(eventName, (event) => {
      event.stopPropagation();
      handler(event);
    }, { capture: true });
  }

  _containDialogWheel(event) {
    const dialog = event.currentTarget;
    const atTop = dialog.scrollTop <= 0 && event.deltaY < 0;
    const atBottom = dialog.scrollTop + dialog.clientHeight >= dialog.scrollHeight - 1 && event.deltaY > 0;
    if (atTop || atBottom) event.preventDefault();
    event.stopPropagation();
  }

  _containDialogTouchStart(event) {
    event.stopPropagation();
    this._dialogTouchY = event.touches?.[0]?.clientY ?? null;
  }

  _containDialogTouchMove(event) {
    const dialog = event.currentTarget;
    const currentY = event.touches?.[0]?.clientY;
    if (this._dialogTouchY === null || currentY === undefined) return;
    const deltaY = this._dialogTouchY - currentY;
    const atTop = dialog.scrollTop <= 0 && deltaY < 0;
    const atBottom = dialog.scrollTop + dialog.clientHeight >= dialog.scrollHeight - 1 && deltaY > 0;
    if (atTop || atBottom) event.preventDefault();
    event.stopPropagation();
    this._dialogTouchY = currentY;
  }

  _containBackdropScroll(event) {
    event.preventDefault();
    event.stopPropagation();
  }

  _bindEvents() {
    this.querySelectorAll('[data-action="generate"]').forEach((button) => {
      button.addEventListener('click', () => this._callButton(this.config.generate_button));
    });
    this.querySelectorAll('[data-action="replace"]').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        const day = button.getAttribute('data-day');
        this._callButton(this._replaceButton(day));
      });
    });
    this._bindDetailButtons();
    this.querySelectorAll('[data-action="close"]').forEach((item) => {
      item.addEventListener('click', (event) => {
        if (event.target === item || item.classList.contains('close')) this._closeRecipe();
      });
    });
    const dialog = this.querySelector('.dialog');
    if (dialog) {
      dialog.scrollTop = this._dialogScrollTop;
      dialog.addEventListener('scroll', () => { this._dialogScrollTop = dialog.scrollTop; });
      dialog.addEventListener('wheel', (event) => this._containDialogWheel(event), { capture: true, passive: false });
      dialog.addEventListener('touchstart', (event) => this._containDialogTouchStart(event), { passive: true });
      dialog.addEventListener('touchmove', (event) => this._containDialogTouchMove(event), { capture: true, passive: false });
    }
    const backdrop = this.querySelector('.dialog-backdrop');
    if (backdrop) {
      backdrop.addEventListener('wheel', (event) => this._containBackdropScroll(event), { passive: false });
      backdrop.addEventListener('touchmove', (event) => this._containBackdropScroll(event), { passive: false });
    }
    const search = this.querySelector('#search');
    this._bindFilterControl(search, 'input', (event) => { this._search = event.target.value; this._renderRecipeResults(); });
    const diet = this.querySelector('#diet');
    this._bindFilterControl(diet, 'change', (event) => { this._dietFilter = event.target.value; this._renderRecipeResults(); });
    const category = this.querySelector('#category');
    this._bindFilterControl(category, 'change', (event) => { this._categoryFilter = event.target.value; this._renderRecipeResults(); });
  }

  _styles() {
    return `
      ha-card { padding: 18px; border-radius: 24px; overflow: hidden; }
      .header-row { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:16px; }
      h2 { margin:0; font-size:28px; line-height:1.1; }
      .muted { margin:6px 0 0 0; opacity:.72; }
      .header-action { border:0; border-radius:16px; background:#F28C28; color:white; padding:10px 14px; font-weight:700; cursor:pointer; }
      .grid { display:grid; gap:14px; }
      .week-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
      .recipes-grid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
      .dg-card { --accent:#F28C28; background:#1f1f1f; border-radius:22px; overflow:hidden; border-top:5px solid var(--accent); box-shadow:0 8px 24px rgba(0,0,0,.28); }
      .dg-card-header { display:flex; justify-content:space-between; align-items:center; padding:12px 14px; color:white; font-size:18px; }
      .icon-button { border:0; width:32px; height:32px; border-radius:50%; background:var(--accent); color:white; font-size:18px; cursor:pointer; }
      .recipe-image { width:100%; height:155px; object-fit:cover; display:block; }
      .dg-card-body { padding:14px; color:white; }
      .dg-card h3 { margin:0 0 8px 0; font-size:18px; line-height:1.25; min-height:46px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
      .meta { color:#d0d0d0; font-size:14px; line-height:1.4; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .detail-button { margin-top:14px; width:100%; border:0; border-radius:16px; background:var(--accent); color:white; padding:11px; font-weight:700; cursor:pointer; }
      .filters { display:grid; grid-template-columns: 1.5fr 1fr 1fr; gap:10px; margin-bottom:16px; }
      input, select { border:1px solid rgba(255,255,255,.16); background:rgba(255,255,255,.06); color:var(--primary-text-color); border-radius:14px; padding:10px; }
      .empty { opacity:.7; }
      .dialog-backdrop { position:fixed; inset:0; z-index:999; background:rgba(0,0,0,.6); display:flex; align-items:center; justify-content:center; padding:20px; box-sizing:border-box; overflow:hidden; touch-action:none; }
      .dialog { width:min(760px, 100%); max-height:calc(100vh - 40px); overflow:auto; overscroll-behavior:contain; box-sizing:border-box; background:var(--card-background-color); color:var(--primary-text-color); border-radius:24px; padding:20px; position:relative; box-shadow:0 20px 70px rgba(0,0,0,.5); touch-action:pan-y; }
      .close { position:absolute; top:10px; right:12px; border:0; background:rgba(0,0,0,.45); color:white; border-radius:50%; width:34px; height:34px; font-size:24px; cursor:pointer; }
      .dialog-image { width:100%; max-height:330px; object-fit:cover; border-radius:18px; }
      .dialog h2 { margin-top:18px; }
      .dialog-meta { opacity:.8; margin-top:8px; }
      .description { opacity:.85; }
      .dialog ul { padding-left:22px; }
      @media (max-width: 700px) { .filters { grid-template-columns:1fr; } ha-card { padding:12px; } }
    `;
  }
}

customElements.define('dinner-genie-card', DinnerGenieCard);
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'dinner-genie-card',
  name: 'Dinner Genie Card',
  description: 'Weekmenu en recepten voor Dinner Genie',
});
