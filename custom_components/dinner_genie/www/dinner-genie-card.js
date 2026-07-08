
const DINNER_GENIE_CARD_VERSION = '2.4.3';
const DINNER_GENIE_CARD_TAG = 'dinner-genie-card';
const DINNER_GENIE_CARD_V2_TAG = 'dinner-genie-card-v2';
const DINNER_GENIE_CARD_VERSIONED_TAG = 'dinner-genie-card-v239';

class DinnerGenieCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    console.info(`Dinner Genie Card v${DINNER_GENIE_CARD_VERSION}`);
  }

  disconnectedCallback() {
    this._unlockPageScroll();
  }

  setConfig(config) {
    this.config = {
      mode: 'week',
      max_days: 7,
      dashboard_path: '/dinner-genie',
      generate_button: 'button.dinner_genie_genereer_weekmenu',
      days_entity: 'number.dinner_genie_aantal_dagen',
      recipes_entity: 'sensor.dinner_genie_recepten',
      debug: false,
      preview: false,
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
    if (this.config.preview) {
      requestAnimationFrame(() => this.render());
    }
  }

  set hass(hass) {
    this._hass = hass;
    const signature = this._renderSignature();
    if (this._rendered && this._isInteracting()) {
      return;
    }
    if (!this._rendered || signature !== this._lastRenderSignature) {
      this.render();
    }
  }

  getCardSize() {
    return this.config?.mode === 'recipes' ? 6 : 4;
  }

  static getStubConfig() {
    return {
      type: `custom:${DINNER_GENIE_CARD_V2_TAG}`,
      mode: 'week',
      title: '🍽️ Weekmenu',
      max_days: 1,
      preview: true,
    };
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

  _weekDayCount() {
    const configuredMax = Number(this.config.max_days || 7);
    const state = this._state(this.config.days_entity);
    const entityDays = Number(state?.state);
    const inferredDays = this._inferredAvailableDayCount(configuredMax);
    const days = Number.isFinite(entityDays) && entityDays > 0 ? entityDays : inferredDays;
    return Math.min(7, Math.max(1, Math.trunc(days)));
  }

  _inferredAvailableDayCount(configuredMax) {
    let lastAvailableDay = 0;
    for (let day = 1; day <= Math.min(7, configuredMax); day += 1) {
      const state = this._state(this._dayEntity(day));
      if (state && !['unavailable', 'unknown'].includes(state.state)) {
        lastAvailableDay = day;
      }
    }
    return lastAvailableDay || configuredMax;
  }

  _callButton(entityId) {
    const resolvedEntityId = this._resolveButtonEntity(entityId);
    if (!resolvedEntityId || !this._hass) {
      console.warn(`Dinner Genie Card v${DINNER_GENIE_CARD_VERSION}: button entity niet gevonden`, entityId);
      return;
    }
    this._hass.callService('button', 'press', { entity_id: resolvedEntityId });
  }

  _resolveButtonEntity(entityId) {
    if (entityId && this._state(entityId)) return entityId;
    if (!this._hass?.states) return entityId;

    const preferred = [
      'button.dinner_genie_genereer_weekmenu',
      'button.dinner_genie_generate_weekmenu',
    ];
    const preferredMatch = preferred.find((candidate) => this._state(candidate));
    if (preferredMatch) return preferredMatch;

    const entries = Object.entries(this._hass.states);
    const generateButton = entries.find(([candidate, state]) => {
      if (!candidate.startsWith('button.')) return false;
      const haystack = `${candidate} ${state?.attributes?.friendly_name || ''}`.toLowerCase();
      return haystack.includes('dinner_genie') && (
        haystack.includes('genereer') ||
        haystack.includes('generate') ||
        haystack.includes('weekmenu') ||
        haystack.includes('week_menu')
      );
    });
    return generateButton?.[0] || entityId;
  }

  _isInteracting() {
    if (this._selectedRecipe) return true;
    const activeElement = this.shadowRoot?.activeElement;
    return ['search', 'diet', 'category'].includes(activeElement?.id);
  }

  _lockPageScroll() {
    if (this._pageScrollLocked) return;
    this._pageScrollLocked = true;
    this._previousBodyOverflow = document.body.style.overflow;
    this._previousDocumentOverflow = document.documentElement.style.overflow;
    document.body.style.overflow = 'hidden';
    document.documentElement.style.overflow = 'hidden';
  }

  _unlockPageScroll() {
    if (!this._pageScrollLocked) return;
    document.body.style.overflow = this._previousBodyOverflow || '';
    document.documentElement.style.overflow = this._previousDocumentOverflow || '';
    this._pageScrollLocked = false;
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

    const maxDays = this._weekDayCount();
    const daysState = this._state(this.config.days_entity);
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
      days_entity: this.config.days_entity,
      days_state: daysState?.state || '',
      days,
    });
  }

  _recipeFromEntity(entityId) {
    const state = this._state(entityId);
    if (!state && this.config?.preview) return this._previewRecipe(entityId);
    if (!state) return null;
    return { state: state.state, entity_id: entityId, ...(state.attributes || {}) };
  }

  _allRecipes() {
    if (this.config?.preview) return [this._previewRecipe('preview_recipe')];
    const state = this._state(this.config.recipes_entity);
    const recipes = state?.attributes?.recipes;
    return Array.isArray(recipes) ? recipes : [];
  }

  _previewRecipe(entityId) {
    return {
      entity_id: entityId,
      state: 'spaghetti spinazie',
      name: 'spaghetti spinazie',
      prep_time: '15',
      diet_type: 'vegan',
      category: 'pasta, vegan',
      description: 'Romige pasta met spinazie, tomaat en een frisse kruidige saus.',
      display_image: '/api/dinner_genie/assets/placeholder_recipe.png',
      ingredients_formatted: ['spaghetti', 'spinazie', 'tomaat', 'vegan roomsaus'],
      instructions: 'Kook de pasta. Bak de groenten kort aan en meng alles met de saus.',
    };
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
    this._lockPageScroll();
    this.render();
  }

  _closeRecipe() {
    this._selectedRecipe = null;
    this._dialogScrollTop = 0;
    this._unlockPageScroll();
    this.render();
  }

  _renderMealCard(recipe, day, color) {
    const title = this._escape(this._recipeTitle(recipe));
    const prep = this._escape(recipe?.prep_time || '');
    const diet = this._escape(recipe?.diet_type || 'geen dieet');
    const category = this._escape(recipe?.category || '');
    const categoryHtml = category ? `🏷️ ${category}` : '&nbsp;';
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
          <div class="meta category-meta">${categoryHtml}</div>
          <button class="detail-button" data-action="details" data-entity="${this._escape(recipe?.entity_id || '')}" data-recipe-id="${this._escape(recipe?.recipe_id || recipe?.id || '')}">Details bekijken</button>
        </div>
      </article>
    `;
  }

  _renderWeek() {
    const colors = ['#F28C28', '#5BAE5B', '#4A90E2', '#8E6CCF', '#D96C6C', '#46B8B8', '#D9B44A'];
    const maxDays = this._weekDayCount();
    const cards = [];
    for (let day = 1; day <= maxDays; day += 1) {
      const recipe = this._recipeFromEntity(this._dayEntity(day));
      if (!recipe || ['unavailable', 'unknown'].includes(recipe.state)) continue;
      cards.push(this._renderMealCard(recipe, day, colors[day - 1] || '#F28C28'));
    }
    const debug = this.config.debug ? this._renderDebug(maxDays, cards.length) : '';
    return `
      <ha-card>
        ${debug}
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

  _renderDebug(maxDays, visibleCards) {
    const daysState = this._state(this.config.days_entity);
    return `
      <div class="debug">
        Card v${DINNER_GENIE_CARD_VERSION} | ${this.config.days_entity}: ${this._escape(daysState?.state || 'niet gevonden')} | dagen: ${maxDays} | kaarten: ${visibleCards}
      </div>
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
    if (!this.config || (!this._hass && !this.config.preview)) return;
    const root = this.shadowRoot || this;
    const activeElement = root.activeElement || (this.contains(document.activeElement) ? document.activeElement : null);
    const activeId = activeElement?.id || '';
    const selectionStart = activeElement && 'selectionStart' in activeElement ? activeElement.selectionStart : null;
    const selectionEnd = activeElement && 'selectionEnd' in activeElement ? activeElement.selectionEnd : null;
    const dialogScrollTop = root.querySelector('.dialog')?.scrollTop ?? this._dialogScrollTop;
    const mode = this.config.mode || 'week';
    root.innerHTML = `
      <style>${this._styles()}</style>
      ${mode === 'recipes' ? this._renderRecipes() : this._renderWeek()}
    `;
    this._bindEvents();
    this._restoreRenderState(activeId, selectionStart, selectionEnd, dialogScrollTop);
    this._lastRenderSignature = this._renderSignature();
    this._rendered = true;
  }

  _restoreRenderState(activeId, selectionStart, selectionEnd, dialogScrollTop) {
    const root = this.shadowRoot || this;
    const dialog = root.querySelector('.dialog');
    if (dialog) {
      this._dialogScrollTop = dialogScrollTop;
      dialog.scrollTop = dialogScrollTop;
    }

    if (!activeId) return;
    const activeElement = root.querySelector(`#${activeId}`);
    if (!activeElement) return;

    activeElement.focus({ preventScroll: true });
    if (selectionStart !== null && selectionEnd !== null && 'setSelectionRange' in activeElement) {
      activeElement.setSelectionRange(selectionStart, selectionEnd);
    }

    requestAnimationFrame(() => {
      const refreshedElement = root.querySelector(`#${activeId}`);
      if (!refreshedElement) return;
      refreshedElement.focus({ preventScroll: true });
      if (selectionStart !== null && selectionEnd !== null && 'setSelectionRange' in refreshedElement) {
        refreshedElement.setSelectionRange(selectionStart, selectionEnd);
      }
    });
  }

  _renderRecipeResults() {
    const recipes = this._filteredRecipes();
    const root = this.shadowRoot || this;
    const count = root.querySelector('[data-role="recipe-count"]');
    if (count) count.textContent = `${recipes.length} van ${this._allRecipes().length} recepten`;

    const grid = root.querySelector('[data-role="recipe-grid"]');
    if (!grid) return;
    grid.innerHTML = recipes.map((recipe) => this._renderMealCard(recipe, null, '#F28C28')).join('') || '<p class="empty">Geen recepten gevonden.</p>';
    this._bindDetailButtons(grid);
  }

  _bindDetailButtons(root = this.shadowRoot || this) {
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
    control.addEventListener('blur', () => {
      setTimeout(() => {
        if (!this._isInteracting() && this._renderSignature() !== this._lastRenderSignature) {
          this.render();
        }
      }, 0);
    });
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
    if (event.target !== event.currentTarget) return;
    event.preventDefault();
    event.stopPropagation();
  }

  _bindEvents() {
    const root = this.shadowRoot || this;
    root.querySelectorAll('[data-action="generate"]').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        this._callButton(this.config.generate_button);
      });
    });
    root.querySelectorAll('[data-action="replace"]').forEach((button) => {
      button.addEventListener('click', (event) => {
        event.stopPropagation();
        const day = button.getAttribute('data-day');
        this._callButton(this._replaceButton(day));
      });
    });
    this._bindDetailButtons();
    root.querySelectorAll('[data-action="close"]').forEach((item) => {
      item.addEventListener('click', (event) => {
        if (event.target === item || item.classList.contains('close')) this._closeRecipe();
      });
    });
    const dialog = root.querySelector('.dialog');
    if (dialog) {
      dialog.scrollTop = this._dialogScrollTop;
      dialog.addEventListener('scroll', () => { this._dialogScrollTop = dialog.scrollTop; });
      dialog.addEventListener('wheel', (event) => this._containDialogWheel(event), { capture: true, passive: false });
      dialog.addEventListener('touchstart', (event) => this._containDialogTouchStart(event), { passive: true });
      dialog.addEventListener('touchmove', (event) => this._containDialogTouchMove(event), { capture: true, passive: false });
    }
    const backdrop = root.querySelector('.dialog-backdrop');
    if (backdrop) {
      backdrop.addEventListener('wheel', (event) => this._containBackdropScroll(event), { passive: false });
      backdrop.addEventListener('touchmove', (event) => this._containBackdropScroll(event), { passive: false });
    }
    const search = root.querySelector('#search');
    this._bindFilterControl(search, 'input', (event) => { this._search = event.target.value; this._renderRecipeResults(); });
    const diet = root.querySelector('#diet');
    this._bindFilterControl(diet, 'change', (event) => { this._dietFilter = event.target.value; this._renderRecipeResults(); });
    const category = root.querySelector('#category');
    this._bindFilterControl(category, 'change', (event) => { this._categoryFilter = event.target.value; this._renderRecipeResults(); });
  }

  _styles() {
    return `
      ha-card { padding: 18px; border-radius: 24px; overflow: hidden; }
      .header-row { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:16px; }
      h2 { margin:0; font-size:28px; line-height:1.1; }
      .muted { margin:6px 0 0 0; opacity:.72; }
      .debug { margin:-4px 0 12px 0; padding:8px 10px; border-radius:10px; background:rgba(242,140,40,.16); color:var(--primary-text-color); font-size:12px; line-height:1.4; }
      .header-action { border:0; border-radius:16px; background:#F28C28; color:white; padding:10px 14px; font-weight:700; cursor:pointer; }
      .grid { display:grid; gap:14px; align-items:stretch; }
      .grid > * { min-width:0; }
      .week-grid { grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); }
      .recipes-grid { grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); }
      .dg-card { --accent:#F28C28; background:#1f1f1f; border-radius:22px; overflow:hidden; border-top:5px solid var(--accent); box-shadow:0 8px 24px rgba(0,0,0,.28); height:100%; display:flex; flex-direction:column; }
      .dg-card-header { display:flex; justify-content:space-between; align-items:center; padding:12px 14px; color:white; font-size:18px; }
      .icon-button { border:0; width:32px; height:32px; border-radius:50%; background:var(--accent); color:white; font-size:18px; cursor:pointer; }
      .recipe-image { width:100%; height:155px; object-fit:cover; display:block; }
      .dg-card-body { padding:14px; color:white; flex:1; display:flex; flex-direction:column; }
      .dg-card h3 { margin:0 0 8px 0; font-size:18px; line-height:1.25; min-height:46px; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
      .meta { color:#d0d0d0; font-size:14px; line-height:1.4; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .category-meta { min-height:20px; }
      .detail-button { margin-top:auto; width:100%; border:0; border-radius:16px; background:var(--accent); color:white; padding:11px; font-weight:700; cursor:pointer; }
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

if (!customElements.get(DINNER_GENIE_CARD_TAG)) {
  customElements.define(DINNER_GENIE_CARD_TAG, DinnerGenieCard);
} else {
  console.info(`Dinner Genie Card v${DINNER_GENIE_CARD_VERSION} loaded after element was already registered`);
}
class DinnerGenieCardV2 extends DinnerGenieCard {
  static getStubConfig() {
    return DinnerGenieCard.getStubConfig();
  }
}

if (!customElements.get(DINNER_GENIE_CARD_V2_TAG)) {
  customElements.define(DINNER_GENIE_CARD_V2_TAG, DinnerGenieCardV2);
}
if (!customElements.get(DINNER_GENIE_CARD_VERSIONED_TAG)) {
  customElements.define(DINNER_GENIE_CARD_VERSIONED_TAG, class DinnerGenieCardV239 extends DinnerGenieCard {});
}

const isDinnerGeniePickerCard = (card) => {
  const haystack = `${card?.type || ''} ${card?.name || ''} ${card?.description || ''}`.toLowerCase();
  return haystack.includes('dinner-genie-card') ||
    haystack.includes('dinner genie') ||
    haystack.includes('dinner card');
};

const registerDinnerGeniePickerCard = () => {
  window.customCards = (window.customCards || []).filter((card) => !isDinnerGeniePickerCard(card));
  window.customCards.push({
    type: DINNER_GENIE_CARD_V2_TAG,
    name: 'Dinner Genie Card',
    description: 'Weekmenu en receptenoverzicht voor Dinner Genie',
    preview: true,
    documentationURL: 'https://github.com/mhholtkamp/dinner_genie',
  });
};

registerDinnerGeniePickerCard();
window.__dinnerGenieRegisterCustomCard = registerDinnerGeniePickerCard;
setTimeout(registerDinnerGeniePickerCard, 500);
setTimeout(registerDinnerGeniePickerCard, 1500);
setTimeout(registerDinnerGeniePickerCard, 3500);
