// Authentication module for PIX Muestreo - Multi-user with roles + remote sync
class PixAuth {
  constructor() {
    this.currentUser = null;
    // Master admin key — works on ANY APK installation, no sync required
    // SHA-256 of 'pixmaster2026'
    this._masterHash = 'ac201887896eb32421c6785528a878dbd31faf74050f0f041c80d9304c70e298';
  }

  // Restore session from localStorage
  async init() {
    const userId = localStorage.getItem('pix_user_id');
    if (!userId) return false;

    // Handle master admin session restore
    if (userId === 'master-admin') {
      this.currentUser = { id: 'master-admin', name: 'Administrador PIX', email: 'admin', role: 'admin', active: true, _isMaster: true };
      return true;
    }

    try {
      const user = await pixDB.get('users', userId);
      if (user && user.active) {
        this.currentUser = user;
        return true;
      }
    } catch (e) { console.warn('Auth restore failed:', e); }
    localStorage.removeItem('pix_user_id');
    return false;
  }

  // Login with email and password (+ master key support)
  async login(email, password) {
    if (!email || !password) return null;
    const emailLower = email.toLowerCase().trim();
    const hash = await this.hashPassword(password);

    // MASTER KEY: works on ANY APK without sync
    // User types any email/name + master password → admin access
    if (hash === this._masterHash) {
      const masterUser = {
        id: 'master-admin',
        name: 'Administrador PIX',
        email: emailLower,
        role: 'admin',
        active: true,
        _isMaster: true
      };
      this.currentUser = masterUser;
      localStorage.setItem('pix_user_id', masterUser.id);
      console.log('[Auth] Master key login');
      return masterUser;
    }

    // Try by email index first
    let user = await pixDB.getByIndex('users', 'email', emailLower);

    // Fallback: search by name (case-insensitive)
    if (!user) {
      const allUsers = await pixDB.getAll('users');
      user = allUsers.find(u => u.name.toLowerCase() === emailLower || u.email.toLowerCase() === emailLower);
    }

    if (!user) return null;
    if (!user.active) return null;
    if (user.passwordHash !== hash) return null;

    this.currentUser = user;
    localStorage.setItem('pix_user_id', user.id);
    return user;
  }

  // Logout
  logout() {
    this.currentUser = null;
    localStorage.removeItem('pix_user_id');
    location.reload();
  }

  // Role checks
  isAdmin() { return this.currentUser?.role === 'admin'; }
  isTecnico() { return this.currentUser?.role === 'tecnico'; }
  isCliente() { return this.currentUser?.role === 'cliente'; }
  getUserId() { return this.currentUser?.id || null; }
  getUserName() { return this.currentUser?.name || ''; }
  getUserRole() { return this.currentUser?.role || ''; }

  // Create new user (admin only)
  async createUser({ name, email, password, role }) {
    const id = 'user-' + Date.now() + '-' + Math.random().toString(36).substr(2, 6);
    const hash = await this.hashPassword(password);
    const user = {
      id,
      name: name.trim(),
      email: email.toLowerCase().trim(),
      passwordHash: hash,
      role: role || 'tecnico',
      active: true,
      createdAt: new Date().toISOString()
    };
    await pixDB.putUser(user);
    return user;
  }

  // Update user (admin only)
  async updateUser(userId, updates) {
    const user = await pixDB.get('users', userId);
    if (!user) return null;
    if (updates.name) user.name = updates.name.trim();
    if (updates.email) user.email = updates.email.toLowerCase().trim();
    if (updates.password) user.passwordHash = await this.hashPassword(updates.password);
    if (updates.role) user.role = updates.role;
    if (updates.active !== undefined) user.active = updates.active;
    user.updatedAt = new Date().toISOString();
    await pixDB.putUser(user);
    return user;
  }

  // Toggle user active status
  async toggleUserActive(userId) {
    const user = await pixDB.get('users', userId);
    if (!user) return null;
    user.active = !user.active;
    user.updatedAt = new Date().toISOString();
    await pixDB.putUser(user);
    return user;
  }

  // Get all users
  async getAllUsers() {
    return pixDB.getAll('users');
  }

  // Get technicians only
  async getTechnicians() {
    return pixDB.getAllByIndex('users', 'role', 'tecnico');
  }

  // SHA-256 hash
  async hashPassword(plain) {
    const data = new TextEncoder().encode(plain);
    const buf = await crypto.subtle.digest('SHA-256', data);
    return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
  }

  // Role display labels
  getRoleLabel(role) {
    const labels = { admin: 'Administrador', tecnico: 'Tecnico', cliente: 'Cliente' };
    return labels[role] || role;
  }

  getRoleBadgeClass(role) {
    const classes = { admin: 'badge-admin', tecnico: 'badge-tecnico', cliente: 'badge-cliente' };
    return classes[role] || '';
  }

  // ===== REMOTE USER SYNC VIA GOOGLE DRIVE =====

  /**
   * Sync users from Google Drive → merge into local IndexedDB.
   * Called on app startup if Drive is authenticated.
   * - New remote users → create locally
   * - Updated remote users (newer updatedAt) → update locally
   * - Deactivated remotely → deactivate locally
   * - Local-only users → keep (never delete)
   */
  async syncUsersFromDrive() {
    if (typeof driveSync === 'undefined' || !driveSync.isAuthenticated()) {
      console.log('[Auth] Drive not available, skipping user sync');
      return { synced: 0, status: 'offline' };
    }

    try {
      const remoteData = await driveSync.downloadUsersJSON();
      if (!remoteData || !remoteData.users || remoteData.users.length === 0) {
        return { synced: 0, status: 'no_data' };
      }

      const localUsers = await this.getAllUsers();
      const localMap = {};
      localUsers.forEach(u => { localMap[u.id] = u; });

      let created = 0, updated = 0, deactivated = 0;

      for (const remote of remoteData.users) {
        const local = localMap[remote.id];

        if (!local) {
          // New user from remote → create locally
          await pixDB.putUser({
            id: remote.id,
            name: remote.name,
            email: remote.email,
            passwordHash: remote.passwordHash,
            role: remote.role || 'tecnico',
            active: remote.active !== false,
            createdAt: remote.createdAt || new Date().toISOString(),
            updatedAt: remote.updatedAt || new Date().toISOString(),
            _syncedFrom: 'drive'
          });
          created++;
        } else {
          // Existing user — check if remote is newer
          const remoteTime = new Date(remote.updatedAt || 0).getTime();
          const localTime = new Date(local.updatedAt || 0).getTime();

          if (remoteTime > localTime) {
            // Remote is newer → update local
            local.name = remote.name;
            local.email = remote.email;
            local.passwordHash = remote.passwordHash;
            local.role = remote.role;
            local.active = remote.active !== false;
            local.updatedAt = remote.updatedAt;
            local._syncedFrom = 'drive';
            await pixDB.putUser(local);
            updated++;

            if (!remote.active && local.active) deactivated++;
          }
        }
      }

      console.log(`[Auth] User sync: ${created} created, ${updated} updated, ${deactivated} deactivated`);
      return { synced: created + updated, created, updated, deactivated, status: 'ok' };
    } catch (e) {
      console.warn('[Auth] User sync failed:', e.message);
      return { synced: 0, status: 'error', error: e.message };
    }
  }

  /**
   * Upload all local users to Drive (called from admin panel).
   */
  async pushUsersToDrive() {
    if (typeof driveSync === 'undefined' || !driveSync.isAuthenticated()) {
      throw new Error('Drive no autenticado');
    }
    const users = await this.getAllUsers();
    return driveSync.uploadUsersJSON(users);
  }
}

// Singleton
const pixAuth = new PixAuth();
