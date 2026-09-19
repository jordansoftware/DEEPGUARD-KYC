export const fonts = ['Inter', 'Roboto', 'Open Sans', 'Lato'] as const
export type Font = (typeof fonts)[number]
