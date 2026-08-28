declare module "*.jsx" {
  const value: any;
  export default value;
}

declare module "*.js" {
  const value: any;
  export default value;
}

declare module "*.svg" {
  const src: string;
  export default src;
}

declare module "*.png" {
  const src: string;
  export default src;
}

declare module "virtual:pwa-register" {
  export type RegisterSWOptions = {
    immediate?: boolean;
    onNeedRefresh?: () => void;
    onOfflineReady?: () => void;
    onRegisterError?: (error: unknown) => void;
  };
  export function registerSW(
    options?: RegisterSWOptions
  ): (reloadPage?: boolean) => Promise<void>;
}

