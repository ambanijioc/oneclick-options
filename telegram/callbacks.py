"""
Callback query router and handlers.
Routes inline keyboard button callbacks to appropriate handlers.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram.auth import require_auth
from logger import logger, log_function_call


@require_auth
@log_function_call
async def callback_query_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Route callback queries to appropriate handlers.
    
    Args:
        update: Telegram update
        context: Callback context
    """
    query = update.callback_query
    await query.answer()  # Acknowledge the callback
    
    try:
        callback_data = query.data
        logger.info(f"[callback_query_router] Routing callback: {callback_data}")
        
        # Parse callback data
        parts = callback_data.split(":")
        action = parts[0]
        
        # Route to appropriate handler
        if action == "menu":
            await handle_menu_callback(update, context, parts)
        elif action == "api":
            await handle_api_callback(update, context, parts)
        elif action == "asset":
            await handle_asset_callback(update, context, parts)
        elif action == "expiry":
            await handle_expiry_callback(update, context, parts)
        elif action == "direction":
            await handle_direction_callback(update, context, parts)
        elif action == "strategy":
            await handle_strategy_callback(update, context, parts)
        elif action == "position":
            await handle_position_callback(update, context, parts)
        elif action == "sltp":
            await handle_sltp_callback(update, context, parts)
        elif action == "execute":
            await handle_execute_callback(update, context, parts)
        elif action == "schedule":
            await handle_schedule_callback(update, context, parts)
        elif action == "cancel":
            await handle_cancel_callback(update, context)
        elif action == "ignore":
            pass  # Do nothing for informational buttons
        else:
            logger.warning(f"[callback_query_router] Unknown action: {action}")
            await query.edit_message_text("❌ Unknown action. Please try again.")
        
    except Exception as e:
        logger.error(f"[callback_query_router] Error routing callback: {e}", exc_info=True)
        await query.edit_message_text(
            "❌ An error occurred. Please try /start again."
        )


@log_function_call
async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """
    Handle menu navigation callbacks.
    
    Args:
        update: Telegram update
        context: Callback context
        parts: Split callback data parts
    """
    query = update.callback_query
    
    try:
        menu_action = parts[1] if len(parts) > 1 else "main"
        
        if menu_action == "main":
            from telegram.keyboards import get_main_menu_keyboard
            await query.edit_message_text(
                "🏠 **Main Menu**\n\nSelect an option:",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
        
        elif menu_action == "manage_api":
            from telegram.handlers.api_handler import show_api_management
            await show_api_management(update, context)
        
        elif menu_action == "balance":
            from telegram.handlers.balance_handler import show_balance
            await show_balance(update, context)
        
        elif menu_action == "positions":
            from telegram.handlers.position_handler import show_positions
            await show_positions(update, context)
        
        elif menu_action == "orders":
            from telegram.handlers.order_handler import show_orders
            await show_orders(update, context)
        
        elif menu_action == "sl_tp":
            from telegram.handlers.sl_tp_handler import show_sl_tp_menu
            await show_sl_tp_menu(update, context)
        
        elif menu_action == "history":
            from telegram.handlers.history_handler import show_trade_history
            await show_trade_history(update, context)
        
        elif menu_action == "list_options":
            from telegram.handlers.options_handler import show_options_menu
            await show_options_menu(update, context)
        
        elif menu_action == "straddle_strategy":
            from telegram.handlers.strategy_handler import show_straddle_strategies
            await show_straddle_strategies(update, context)
        
        elif menu_action == "strangle_strategy":
            from telegram.handlers.strategy_handler import show_strangle_strategies
            await show_strangle_strategies(update, context)
        
        elif menu_action == "manual_trade":
            from telegram.handlers.manual_trade_handler import show_manual_trade_menu
            await show_manual_trade_menu(update, context)
        
        elif menu_action == "auto_trade":
            from telegram.handlers.auto_trade_handler import show_auto_trade_menu
            await show_auto_trade_menu(update, context)
        
        elif menu_action == "help":
            from telegram.commands import help_command
            # Convert callback to message-like update
            await query.edit_message_text(
                "📖 **Help & Commands**\n\n"
                "Use /help command for detailed help information.\n\n"
                "Or use the buttons below to navigate:",
                parse_mode='Markdown'
            )
        
    except ImportError as e:
        logger.warning(f"[handle_menu_callback] Handler not yet implemented: {e}")
        await query.edit_message_text(
            f"⚠️ This feature is coming soon!\n\n"
            f"Feature: {menu_action}",
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"[handle_menu_callback] Error: {e}", exc_info=True)
        await query.edit_message_text("❌ An error occurred. Please try again.")


@log_function_call
async def handle_api_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle API management callbacks."""
    query = update.callback_query
    
    try:
        action = parts[1] if len(parts) > 1 else None
        
        if action == "add":
            await query.edit_message_text(
                "➕ **Add New API**\n\n"
                "This feature will guide you through adding Delta Exchange API credentials.\n\n"
                "Coming soon!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"API action: {action}\n\nComing soon!")
        
    except Exception as e:
        logger.error(f"[handle_api_callback] Error: {e}")
        await query.edit_message_text("❌ Error handling API action.")


@log_function_call
async def handle_asset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle asset selection callbacks."""
    query = update.callback_query
    asset = parts[1] if len(parts) > 1 else None
    
    context.user_data['selected_asset'] = asset
    await query.edit_message_text(f"Selected asset: {asset}\n\nProceed with next step...")


@log_function_call
async def handle_expiry_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle expiry selection callbacks."""
    query = update.callback_query
    expiry = parts[1] if len(parts) > 1 else None
    
    context.user_data['selected_expiry'] = expiry
    await query.edit_message_text(f"Selected expiry: {expiry}\n\nProceed with next step...")


@log_function_call
async def handle_direction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle direction selection callbacks."""
    query = update.callback_query
    direction = parts[1] if len(parts) > 1 else None
    
    context.user_data['selected_direction'] = direction
    await query.edit_message_text(f"Selected direction: {direction}\n\nProceed with next step...")


@log_function_call
async def handle_strategy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle strategy management callbacks."""
    query = update.callback_query
    await query.edit_message_text("Strategy management coming soon!")


@log_function_call
async def handle_position_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle position selection callbacks."""
    query = update.callback_query
    await query.edit_message_text("Position management coming soon!")


@log_function_call
async def handle_sltp_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle SL/TP callbacks."""
    query = update.callback_query
    await query.edit_message_text("SL/TP management coming soon!")


@log_function_call
async def handle_execute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle trade execution callbacks."""
    query = update.callback_query
    await query.edit_message_text("Trade execution coming soon!")


@log_function_call
async def handle_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, parts: list):
    """Handle schedule management callbacks."""
    query = update.callback_query
    await query.edit_message_text("Schedule management coming soon!")


@log_function_call
async def handle_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle cancel/back callbacks."""
    query = update.callback_query
    
    from telegram.keyboards import get_main_menu_keyboard
    
    await query.edit_message_text(
        "❌ Action cancelled.\n\n"
        "🏠 Main Menu:",
        reply_markup=get_main_menu_keyboard()
    )
    
    # Clear user data
    context.user_data.clear()


if __name__ == "__main__":
    print("Telegram callbacks module loaded")
    print("Callback router ready")
  
