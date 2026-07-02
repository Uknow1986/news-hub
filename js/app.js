/**
 * 每日国际要闻 - 前端应用逻辑
 * 功能：加载新闻数据、板块切换、搜索、收藏、历史归档
 */

// === 全局状态 ===
let currentSection = 'tech';
let currentData = null;
let searchData = null; // 当前搜索结果
let bookmarks = JSON.parse(localStorage.getItem('newsBookmarks') || '{}');

// 板块配置
const SECTION_NAMES = {
    'tech': '科技产业',
    'americas': '美洲时政',
};

// === 初始化 ===
async function init() {
    await loadAvailableDates();
    await loadLatestData();
    updateBookmarkCount();
}

// === 加载可用日期列表 ===
async function loadAvailableDates() {
    try {
        // 尝试加载日期索引文件
        const response = await fetch('data/index.json');
        if (response.ok) {
            const dates = await response.json();
            populateDateSelect(dates);
            return;
        }
    } catch (e) {
        // 索引文件不存在，使用默认日期
    }

    // 尝试加载今天的数据
    const today = new Date().toLocaleDateString('en-CA', { timeZone: 'Asia/Shanghai' });
    populateDateSelect([today]);
}

function populateDateSelect(dates) {
    const select = document.getElementById('dateSelect');
    select.innerHTML = '';
    dates.forEach((date, i) => {
        const option = document.createElement('option');
        option.value = date;
        // 格式化日期显示
        const d = new Date(date + 'T00:00:00');
        const weekday = ['日','一','二','三','四','五','六'][d.getDay()];
        option.textContent = `${date} (周${weekday})`;
        select.appendChild(option);
    });
    // 默认选中第一个（最新日期）
    if (dates.length > 0) {
        select.value = dates[0];
    }
}

// === 加载指定日期的数据 ===
async function loadDate() {
    const dateSelect = document.getElementById('dateSelect');
    const date = dateSelect.value;
    await loadData(date);
}

// === 加载最新数据 ===
async function loadLatestData() {
    const dateSelect = document.getElementById('dateSelect');
    const date = dateSelect.value;
    await loadData(date);
}

async function loadData(date) {
    if (!date) return;

    try {
        const response = await fetch(`data/${date}.json`);
        if (!response.ok) {
            showError('暂无该日期的新闻数据');
            return;
        }
        currentData = await response.json();
        searchData = null;
        document.getElementById('searchInput').value = '';

        // 更新更新时间
        document.getElementById('updateInfo').textContent =
            `更新于 ${currentData.updated_at} · 共 ${currentData.total} 条`;

        // 更新各板块计数
        for (const section of Object.keys(SECTION_NAMES)) {
            const count = currentData.sections[section]?.articles.length || 0;
            document.getElementById(`count-${section}`).textContent = count;
        }

        renderArticles();
    } catch (e) {
        showError('数据加载失败，请稍后重试');
        console.error(e);
    }
}

// === 板块切换 ===
function switchTab(section) {
    currentSection = section;
    searchData = null;
    document.getElementById('searchInput').value = '';

    // 更新标签状态
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.section === section);
    });

    renderArticles();
}

// === 搜索 ===
function handleSearch() {
    const query = document.getElementById('searchInput').value.trim().toLowerCase();

    if (!query) {
        searchData = null;
    } else {
        searchData = [];
        if (currentData) {
            for (const section of Object.keys(currentData.sections)) {
                for (const article of currentData.sections[section].articles) {
                    const searchText = (
                        article.title_zh + ' ' +
                        article.summary_zh + ' ' +
                        article.title_en + ' ' +
                        article.source
                    ).toLowerCase();
                    if (searchText.includes(query)) {
                        searchData.push({ ...article, section });
                    }
                }
            }
        }
    }

    renderArticles();
}

// === 渲染文章列表 ===
function renderArticles() {
    const container = document.getElementById('articleList');
    const emptyState = document.getElementById('emptyState');

    let articles = [];

    if (searchData !== null) {
        // 搜索模式
        articles = searchData;
    } else if (currentData && currentData.sections) {
        // 正常浏览模式
        const sectionData = currentData.sections[currentSection];
        if (sectionData) {
            articles = sectionData.articles.map(a => ({ ...a, section: currentSection }));
        }
    }

    if (articles.length === 0) {
        container.innerHTML = '';
        emptyState.style.display = 'block';
        if (searchData !== null) {
            emptyState.querySelector('p').textContent = '🔍 没有找到匹配的新闻';
        } else {
            emptyState.querySelector('p').textContent = '📭 今日该板块暂无新闻';
        }
        return;
    }

    emptyState.style.display = 'none';

    container.innerHTML = articles.map(article => {
        const isBookmarked = bookmarks[article.id];
        const sectionClass = `section-${article.section}`;
        const sectionName = SECTION_NAMES[article.section] || '';
        return `
            <div class="article-card ${sectionClass}">
                <div class="article-meta">
                    <span class="source-badge">${article.source}</span>
                    <span class="section-tag">${sectionName}</span>
                    ${article.published ? `<span>· ${article.published}</span>` : ''}
                </div>
                <h3 class="article-title">${article.title_zh}</h3>
                <p class="article-summary">${article.summary_zh}</p>
                <div class="article-footer">
                    <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="article-link">
                        📖 阅读原文
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M7 17l9.2-9.2M17 17V7H7"></path>
                        </svg>
                    </a>
                    <button class="bookmark-toggle ${isBookmarked ? 'active' : ''}"
                            onclick="toggleBookmark('${article.id}', '${article.title_zh}', '${article.source}', '${article.url}', '${article.section}')"
                            title="${isBookmarked ? '取消收藏' : '收藏'}">
                        ${isBookmarked ? '★' : '☆'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// === 收藏功能 ===
function toggleBookmark(id, title, source, url, section) {
    if (bookmarks[id]) {
        delete bookmarks[id];
    } else {
        bookmarks[id] = {
            id,
            title,
            source,
            url,
            section,
            savedAt: new Date().toISOString(),
        };
    }
    localStorage.setItem('newsBookmarks', JSON.stringify(bookmarks));
    updateBookmarkCount();
    renderArticles();
}

function updateBookmarkCount() {
    const count = Object.keys(bookmarks).length;
    document.getElementById('bookmarkCount').textContent = count;
}

// === 收藏弹窗 ===
function showBookmarks() {
    const modal = document.getElementById('bookmarkModal');
    const list = document.getElementById('bookmarkList');
    const bookmarkItems = Object.values(bookmarks);

    if (bookmarkItems.length === 0) {
        list.innerHTML = '<div class="bookmark-empty">还没有收藏的新闻<br>点击 ☆ 收藏你感兴趣的文章</div>';
    } else {
        // 按收藏时间倒序
        bookmarkItems.sort((a, b) => new Date(b.savedAt) - new Date(a.savedAt));
        list.innerHTML = bookmarkItems.map(b => `
            <div class="bookmark-item">
                <div class="bookmark-item-title">${b.title}</div>
                <div class="bookmark-item-meta">
                    <span class="source-badge">${b.source}</span>
                    <span>${SECTION_NAMES[b.section] || ''}</span>
                    <span>· 收藏于 ${new Date(b.savedAt).toLocaleDateString('zh-CN')}</span>
                </div>
                <div style="margin-top: 6px;">
                    <a href="${b.url}" target="_blank" rel="noopener noreferrer" class="bookmark-item-link">📖 阅读原文</a>
                    <button onclick="removeBookmark('${b.id}')" style="background:none;border:none;color:#999;cursor:pointer;font-size:13px;margin-left:12px;">🗑 移除</button>
                </div>
            </div>
        `).join('');
    }

    modal.style.display = 'flex';
}

function removeBookmark(id) {
    delete bookmarks[id];
    localStorage.setItem('newsBookmarks', JSON.stringify(bookmarks));
    updateBookmarkCount();
    showBookmarks();
    renderArticles();
}

function closeModal() {
    document.getElementById('bookmarkModal').style.display = 'none';
}

// 点击弹窗外关闭
document.addEventListener('click', function(e) {
    const modal = document.getElementById('bookmarkModal');
    if (e.target === modal) {
        closeModal();
    }
});

// ESC 键关闭弹窗
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
});

// === 错误提示 ===
function showError(msg) {
    const container = document.getElementById('articleList');
    const emptyState = document.getElementById('emptyState');
    container.innerHTML = '';
    emptyState.style.display = 'block';
    emptyState.querySelector('p').textContent = msg;
}

// === 启动 ===
init();
