const state = {
  token: localStorage.getItem('token'),
  userEmail: localStorage.getItem('userEmail') || null,
  pending: null,
  page: 1,
  pageSize: 5,
};

function jsonHeaders(token) {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  return headers;
}

function appendMessage(text, sender = 'bot') {
  const history = document.getElementById('chat_history');
  const message = document.createElement('div');
  message.className = `chat-message ${sender}`;
  message.innerText = text;
  history.appendChild(message);
  history.scrollTop = history.scrollHeight;
}

function botSay(text) {
  appendMessage(text, 'bot');
}

function userSay(text) {
  appendMessage(text, 'user');
}

function setStatus(text, isError = false) {
  const target = document.getElementById('status');
  target.innerText = text;
  target.className = isError ? 'status status-error' : 'status';
}

function updateDashboardUI() {
  document.getElementById('dashboard').classList.toggle('hidden', !state.token);
}

function saveSession(token, email) {
  state.token = token;
  state.userEmail = email;
  localStorage.setItem('token', token);
  localStorage.setItem('userEmail', email);
  updateDashboardUI();
}

function clearSession() {
  state.token = null;
  state.userEmail = null;
  localStorage.removeItem('token');
  localStorage.removeItem('userEmail');
  updateDashboardUI();
}

async function apiRequest(method, path, data) {
  const options = { method, headers: jsonHeaders(state.token) };
  if (data) options.body = JSON.stringify(data);
  const res = await fetch(path, options);
  const payload = await res.json().catch(() => null);
  return { ok: res.ok, payload, status: res.status };
}

function resetChatInput() {
  document.getElementById('chat_input').value = '';
}

const WHATSAPP_NUMBER = '';
const WHATSAPP_MESSAGE = encodeURIComponent('Hello Expense AI Bot, I want to login or register and sync expenses.');

function getWhatsAppUrl() {
  if (WHATSAPP_NUMBER) {
    return `https://wa.me/${WHATSAPP_NUMBER}?text=${WHATSAPP_MESSAGE}`;
  }
  return `whatsapp://send?text=${WHATSAPP_MESSAGE}`;
}

function openWhatsApp() {
  const url = getWhatsAppUrl();
  botSay('Opening WhatsApp...');
  const opened = window.open(url, '_blank', 'noopener');
  if (!opened) {
    window.location.href = 'https://web.whatsapp.com/';
  }
}

async function shareLink() {
  const shareData = {
    title: 'Expense AI Chat Bot',
    text: 'Add the Expense AI chat bot on WhatsApp to manage expenses from chat.',
    url: window.location.href,
  };

  if (navigator.share) {
    try {
      await navigator.share(shareData);
      botSay('Share prompt opened.');
    } catch (error) {
      botSay('Share cancelled or unavailable.');
    }
    return;
  }

  await navigator.clipboard.writeText(window.location.href);
  botSay('Link copied to clipboard. Share it to add the WhatsApp bot.');
}

function showHelp() {
  botSay('Commands you can use:');
  botSay('• register name email password');
  botSay('• login email password');
  botSay('• logout');
  botSay('• create [amount merchant category description type]');
  botSay('• list');
  botSay('• show dashboard');
  botSay('• hide dashboard');
  botSay('• open whatsapp');
  botSay('• help');
  botSay('You can also click Add bot on WhatsApp to open the bot chat.');
  botSay('If you type only `create`, I will ask you step-by-step.');
}

function parseCommand(input) {
  const text = input.trim();
  if (!text) return;
  if (state.pending) return handlePending(text);

  const tokens = text.split(/\s+/);
  const command = tokens[0].toLowerCase();

  if (command === 'help') {
    showHelp();
  } else if (command === 'register') {
    if (tokens.length >= 4) {
      doRegister(tokens[1], tokens[2], tokens.slice(3).join(' '));
    } else {
      state.pending = { flow: 'register', step: 'name', data: {} };
      botSay('Okay, let us register. What is your name?');
    }
  } else if (command === 'login') {
    if (tokens.length >= 3) {
      doLogin(tokens[1], tokens.slice(2).join(' '));
    } else {
      state.pending = { flow: 'login', step: 'email', data: {} };
      botSay('Please enter your email.');
    }
  } else if (command === 'logout') {
    if (!state.token) {
      botSay('You are not logged in.');
      return;
    }
    clearSession();
    botSay('You have been logged out.');
  } else if (command === 'create') {
    if (!state.token) {
      botSay('Please login first to create an expense.');
      return;
    }
    if (tokens.length >= 6) {
      const amount = parseFloat(tokens[1]);
      const merchant = tokens[2];
      const category = tokens[3];
      const description = tokens[4];
      const type = tokens.slice(5).join(' ') || 'Expense';
      doCreateExpense({ amount, merchant, category, description, type });
    } else {
      state.pending = { flow: 'create', step: 'amount', data: {} };
      botSay('Creating an expense. What is the amount?');
    }
  } else if (command === 'list') {
    if (!state.token) {
      botSay('Please login first.');
      return;
    }
    doListExpenses();
  } else if (command === 'show' && tokens[1] === 'dashboard') {
    if (!state.token) {
      botSay('Login first, then type show dashboard.');
      return;
    }
    updateDashboardUI();
    await loadDashboard();
    botSay('Dashboard is visible now.');
  } else if ((command === 'open' && tokens[1] === 'whatsapp') || command === 'whatsapp') {
    openWhatsApp();
  } else if (command === 'share') {
    await shareLink();
  } else if (command === 'hide' && tokens[1] === 'dashboard') {
    document.getElementById('dashboard').classList.add('hidden');
    botSay('Dashboard hidden.');
  } else if (command === 'delete') {
    if (!state.token) {
      botSay('Please login first.');
      return;
    }
    const id = tokens[1];
    if (!id) {
      botSay('Please specify the expense ID. Example: delete 1');
      return;
    }
    doDeleteExpense(id);
  } else {
    botSay('I did not understand that command. Type help to see available options.');
  }
}

async function handlePending(text) {
  const pending = state.pending;
  if (!pending) return;

  if (pending.flow === 'register') {
    if (pending.step === 'name') {
      pending.data.name = text;
      pending.step = 'email';
      botSay('Great. What is your email?');
    } else if (pending.step === 'email') {
      pending.data.email = text;
      pending.step = 'password';
      botSay('And the password?');
    } else if (pending.step === 'password') {
      pending.data.password = text;
      state.pending = null;
      doRegister(pending.data.name, pending.data.email, pending.data.password);
    }
  } else if (pending.flow === 'login') {
    if (pending.step === 'email') {
      pending.data.email = text;
      pending.step = 'password';
      botSay('Now enter your password.');
    } else if (pending.step === 'password') {
      pending.data.password = text;
      state.pending = null;
      doLogin(pending.data.email, pending.data.password);
    }
  } else if (pending.flow === 'create') {
    if (pending.step === 'amount') {
      pending.data.amount = parseFloat(text);
      if (Number.isNaN(pending.data.amount) || pending.data.amount <= 0) {
        botSay('Please send a valid number for amount.');
        return;
      }
      pending.step = 'merchant';
      botSay('Merchant name?');
    } else if (pending.step === 'merchant') {
      pending.data.merchant = text;
      pending.step = 'category';
      botSay('Category?');
    } else if (pending.step === 'category') {
      pending.data.category = text;
      pending.step = 'description';
      botSay('Description?');
    } else if (pending.step === 'description') {
      pending.data.description = text;
      pending.step = 'type';
      botSay('Type (Expense or Income)?');
    } else if (pending.step === 'type') {
      pending.data.type = text || 'Expense';
      state.pending = null;
      doCreateExpense(pending.data);
    }
  }
}

async function doRegister(name, email, password) {
  const { ok, payload } = await apiRequest('POST', '/users/register', { name, email, password });
  if (ok) {
    botSay('Registration successful. Now login with: login email password');
  } else {
    botSay(payload?.detail || 'Registration failed.');
  }
}

async function doLogin(email, password) {
  const { ok, payload } = await apiRequest('POST', '/users/login', { email, password });
  if (ok && payload?.access_token) {
    saveSession(payload.access_token, email);
    botSay('Logged in successfully. Type show dashboard or list to continue.');
    updateDashboardUI();
    await loadDashboard();
  } else {
    botSay(payload?.detail || 'Login failed.');
  }
}

async function doCreateExpense(data) {
  const { ok, payload } = await apiRequest('POST', '/expenses/', data);
  if (ok) {
    botSay('Expense created: ' + payload.merchant + ' for $' + payload.amount);
    if (document.getElementById('dashboard').classList.contains('hidden') === false) {
      loadDashboard();
    }
  } else {
    botSay(payload?.detail || 'Failed to create expense.');
  }
}

async function doListExpenses() {
  const { ok, payload } = await apiRequest('GET', `/expenses/?page=1&page_size=20`);
  if (ok && payload?.items) {
    if (!payload.items.length) {
      botSay('No expenses found. Create one using create.');
      return;
    }
    botSay('Here are your latest expenses:');
    payload.items.forEach((expense) => {
      botSay(`${expense.id}. ${expense.merchant} - $${expense.amount} (${expense.category})`);
    });
  } else {
    botSay(payload?.detail || 'Unable to load expenses.');
  }
}

async function doDeleteExpense(id) {
  const { ok, payload } = await apiRequest('DELETE', `/expenses/${id}`);
  if (ok) {
    botSay('Expense deleted successfully.');
    loadDashboard();
  } else {
    botSay(payload?.detail || 'Failed to delete expense.');
  }
}

async function loadDashboard() {
  if (!state.token) return;
  const { ok, payload } = await apiRequest('GET', `/expenses/?page=1&page_size=20`);
  if (!ok || !payload?.items) {
    document.getElementById('dashboard_summary').innerText = 'Unable to load dashboard.';
    return;
  }
  document.getElementById('dashboard_summary').innerText = `Logged in as ${state.userEmail}. Showing ${payload.total} expense(s).`;
  const list = document.getElementById('dashboard_expenses');
  list.innerHTML = '';
  if (!payload.items.length) {
    list.innerHTML = '<p class="empty">No expenses yet.</p>';
    return;
  }
  payload.items.forEach((expense) => {
    const item = document.createElement('div');
    item.className = 'expense-card';
    item.innerHTML = `<strong>${expense.merchant}</strong><div class="meta">$${expense.amount.toFixed(2)} • ${expense.category} • ${expense.type}</div><p class="desc">${expense.description || 'No description'}</p>`;
    list.appendChild(item);
  });
}

async function handleSend() {
  const input = document.getElementById('chat_input');
  const text = input.value.trim();
  if (!text) return;
  userSay(text);
  resetChatInput();
  setStatus('');
  await parseCommand(text);
}

function attachEvents() {
  document.getElementById('btn_send').addEventListener('click', handleSend);
  document.getElementById('btn_whatsapp').addEventListener('click', openWhatsApp);
  document.getElementById('btn_share').addEventListener('click', shareLink);
  document.getElementById('chat_input').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleSend();
    }
  });
}

function init() {
  attachEvents();
  updateDashboardUI();
  botSay('Hi! I am your expense bot. Type help to get started.');
  if (state.token && state.userEmail) {
    botSay(`Welcome back, ${state.userEmail}. Type show dashboard or list.`);
  }
}

init();
