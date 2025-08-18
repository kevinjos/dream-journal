import { defineStore, acceptHMRUpdate } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: localStorage.getItem('theme') === 'light' ? false : true, // Default to dark
  }),

  getters: {
    currentTheme: (state): 'dark' | 'light' => state.isDark ? 'dark' : 'light',
  },

  actions: {
    toggleTheme(): void {
      this.isDark = !this.isDark
      this.persistTheme()
    },

    setTheme(theme: 'dark' | 'light'): void {
      this.isDark = theme === 'dark'
      this.persistTheme()
    },

    persistTheme(): void {
      // Persist theme preference
      localStorage.setItem('theme', this.currentTheme)
    },

    // This will be called from components that have access to $q
    getThemeState(): boolean {
      return this.isDark
    }
  },
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useThemeStore, import.meta.hot))
}