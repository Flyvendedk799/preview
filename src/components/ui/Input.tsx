import { InputHTMLAttributes, TextareaHTMLAttributes, forwardRef, ReactNode } from 'react'
import { ExclamationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  helperText?: string
  success?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  leftAddon?: string
  rightAddon?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ 
    label, 
    error, 
    helperText, 
    success,
    leftIcon,
    rightIcon,
    leftAddon,
    rightAddon,
    className = '', 
    ...props 
  }, ref) => {
    const hasError = Boolean(error)
    const hasSuccess = success && !hasError
    
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-secondary-700 mb-1.5">
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        
        <div className="relative flex">
          {/* Left addon */}
          {leftAddon && (
            <span className="inline-flex items-center px-3 text-sm text-secondary-500 bg-secondary-50 border border-r-0 border-secondary-300 rounded-l-lg">
              {leftAddon}
            </span>
          )}
          
          {/* Input wrapper */}
          <div className="relative flex-1">
            {/* Left icon */}
            {leftIcon && (
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-secondary-400">
                {leftIcon}
              </div>
            )}
            
            <input
              ref={ref}
              className={`
                input
                ${hasError ? 'input-error' : ''}
                ${hasSuccess ? 'input-success' : ''}
                ${leftIcon ? 'pl-10' : ''}
                ${rightIcon || hasError || hasSuccess ? 'pr-10' : ''}
                ${leftAddon ? 'rounded-l-none' : ''}
                ${rightAddon ? 'rounded-r-none' : ''}
                ${className}
              `}
              {...props}
            />
            
            {/* Right icon / status icon */}
            <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
              {hasError && <ExclamationCircleIcon className="w-5 h-5 text-error-500" />}
              {hasSuccess && <CheckCircleIcon className="w-5 h-5 text-success-500" />}
              {!hasError && !hasSuccess && rightIcon && (
                <span className="text-secondary-400">{rightIcon}</span>
              )}
            </div>
          </div>
          
          {/* Right addon */}
          {rightAddon && (
            <span className="inline-flex items-center px-3 text-sm text-secondary-500 bg-secondary-50 border border-l-0 border-secondary-300 rounded-r-lg">
              {rightAddon}
            </span>
          )}
        </div>
        
        {/* Helper/Error text */}
        {(error || helperText) && (
          <p className={`mt-1.5 text-sm ${hasError ? 'text-error-500' : 'text-secondary-500'}`}>
            {error || helperText}
          </p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input

// Textarea component
interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  helperText?: string
  showCount?: boolean
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, helperText, showCount, maxLength, className = '', value, ...props }, ref) => {
    const hasError = Boolean(error)
    const currentLength = typeof value === 'string' ? value.length : 0
    
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-secondary-700 mb-1.5">
            {label}
            {props.required && <span className="text-error-500 ml-1">*</span>}
          </label>
        )}
        
        <textarea
          ref={ref}
          value={value}
          maxLength={maxLength}
          className={`textarea ${hasError ? 'input-error' : ''} ${className}`}
          {...props}
        />
        
        <div className="flex justify-between mt-1.5">
          {(error || helperText) && (
            <p className={`text-sm ${hasError ? 'text-error-500' : 'text-secondary-500'}`}>
              {error || helperText}
            </p>
          )}
          {showCount && maxLength && (
            <p className={`text-sm ml-auto ${currentLength >= maxLength ? 'text-error-500' : 'text-secondary-400'}`}>
              {currentLength}/{maxLength}
            </p>
          )}
        </div>
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'

// Search Input component
interface SearchInputProps extends Omit<InputProps, 'leftIcon'> {
  onClear?: () => void
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ onClear, value, ...props }, ref) => {
    return (
      <Input
        ref={ref}
        type="search"
        value={value}
        leftIcon={
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        }
        rightIcon={value && onClear ? (
          <button 
            type="button"
            onClick={onClear}
            className="pointer-events-auto hover:text-secondary-600"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        ) : undefined}
        {...props}
      />
    )
  }
)

SearchInput.displayName = 'SearchInput'
