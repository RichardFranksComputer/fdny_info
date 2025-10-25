
/* WARNING: Type propagation algorithm not settling */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* RescueBot main loop - manages rescue operations based on difficulty
   DIFFICULTY EFFECTS:
   1. difficulty_threshold (DAT_00502afc) controls rescue activation frequency
      - Higher threshold = more frequent rescue attempts
   2. victim_count_multiplier varies by game mode/difficulty:
      - Easy mode (0): 0.25x multiplier (fewer victims)
      - Medium mode (1): 0.4x multiplier 
      - Hard mode (2+): 0.8x multiplier (more victims)
   3. max_concurrent_victims = round(random_value * multiplier)
   4. Game states 3,4,5 allow rescues; state 6 blocks all rescues
   5. rescue_attempt_counter must exceed threshold to trigger rescue spawn */

void __fastcall rescuebot_main?(struct_rescuebot rescuebot)

{
  undefined4 *puVar1;
  void *pvVar2;
  undefined4 uVar3;
  int max_concurrent_victims;
  uint uVar4;
  int *piVar5;
  struct_rescuebot *bot;
  int extraout_ECX;
  int extraout_ECX_00;
  ulonglong uVar6;
  char *pcVar7;
  int iVar8;
  int *difficulty_settings_ptr;
  int stack_locals [29];
  void *saved_exception_list;
  undefined1 *puStack_8;
  undefined4 exception_state;
  struct_game_world *game_world;
  
  exception_state = 0xffffffff;
  puStack_8 = &LAB_004d097b;
  saved_exception_list = ExceptionList;
  if ((char)bot->is_active_l != '\0') {
    game_world = (struct_game_world *)DAT_00503a78[0xc];
    difficulty_settings_ptr = DAT_00502afc;
    if (game_world->game_or_level_state_l != 6) {
      ExceptionList = &saved_exception_list;
      if ((bot->has_victim_l != 0) &&
         (ExceptionList = &saved_exception_list,
         bot->current_location_id_or_dropoff_point_l < DAT_00502afc)) {
        ExceptionList = &saved_exception_list;
        check_level_complete_and_activate_exits(game_world);
        puVar1 = create_log_message(stack_locals + 7,"rescue\\RescueBot.cpp",0x3c);
        exception_state = 0;
        log_message(puVar1 + 7,"RESCUEBOT: Victim dropped off");
        write_log_with_level(puVar1,3);
        exception_state = 0xffffffff;
        cleanup_log_message(stack_locals + 7);
        bot->has_victim_l = 0;
        update_rescue_timers((int)bot);
        set_initial_rescue_timer(extraout_ECX);
      }
      if ((bot->has_victim_l == 0) &&
         (((max_concurrent_victims = game_world->game_or_level_state_l, max_concurrent_victims == 3
           || (max_concurrent_victims == 4)) || (max_concurrent_victims == 5)))) {
        if (DAT_00502a78 != '\0') {
          create_debug_flag_string(stack_locals,"DBG_ACTIVATE_RESCUEBOT");
          piVar5 = stack_locals;
          exception_state = 1;
          pvVar2 = (void *)get_debug_flags_manager(DAT_00503a78);
          uVar3 = check_debug_flag_enabled(pvVar2,piVar5);
          exception_state = 0xffffffff;
          release_string_ref(stack_locals);
          if ((char)uVar3 != '\0') {
            bot->rescue_attempt_counter_l = (int *)((int)difficulty_settings_ptr + 1);
          }
        }
        if (bot->rescue_attempt_counter_l < difficulty_settings_ptr) {
          stack_locals[1] = 0;
          stack_locals[2] = 0;
          stack_locals[3] = 0;
          stack_locals[4] = 0x3fd00000;
          stack_locals[5] = 0x9999999a;
          stack_locals[6] = 0x3fd99999;
          uVar6 = get_rounded_number();
          max_concurrent_victims = (int)uVar6;
          if (game_world->active_victim_count_l < max_concurrent_victims) {
            find_assign_victim((int)bot);
          }
          else {
            puVar1 = create_log_message(stack_locals + 7,"rescue\\RescueBot.cpp",100);
            iVar8 = 3;
            pcVar7 = " victims";
            exception_state = 2;
            pvVar2 = (void *)string_append_cstr(puVar1,"RESCUEBOT: Exceeded maximum of ");
            pvVar2 = (void *)string_append_int(pvVar2,max_concurrent_victims);
            pvVar2 = (void *)string_append_cstr(pvVar2,pcVar7);
            write_log_with_level(pvVar2,iVar8);
            exception_state = 0xffffffff;
            cleanup_log_message(stack_locals + 7);
          }
          set_victim_dropoff_timer((int)bot);
        }
        if (bot->message_timer_l < difficulty_settings_ptr) {
          uVar4 = rescuebot_hash_function(*(uint *)(bot->message_data_ptr_l + 4));
          puVar1 = (undefined4 *)get_message_by_hash(&bot->message_data_ptr_l,uVar4);
          if (difficulty_init_likely == '\0') {
            difficulty_init_likely = '\x01';
            difficulty_level_likely = 2;
            DAT_0050190c = 0;
            _DAT_00501910 = 1;
            DAT_00501914 = 0;
          }
          difficulty_settings_ptr = &difficulty_level_likely;
          piVar5 = (int *)*puVar1;
          if (piVar5 != &difficulty_level_likely) {
            *piVar5 = *piVar5 + 1;
            difficulty_settings_ptr = piVar5;
          }
          exception_state = 3;
          piVar5 = get_bot_name(stack_locals + 5);
          exception_state._0_1_ = 4;
          pvVar2 = format_string_with_color(stack_locals + 3,"^(128,128,240)",piVar5);
          exception_state._0_1_ = 5;
          string_append_formatted(pvVar2,stack_locals + 1,":\n^(255,255,255)");
          exception_state._0_1_ = 8;
          release_string_ref(stack_locals + 3);
          exception_state._0_1_ = 7;
          release_string_ref(stack_locals + 5);
          string_append(stack_locals + 1,(char *)(difficulty_settings_ptr + 3));
          display_game_message((void *)(DAT_00503a78[0xc] + 0x5f4),&difficulty_settings_ptr);
          update_rescue_timers((int)bot);
          set_initial_rescue_timer(extraout_ECX_00);
          exception_state = CONCAT31(exception_state._1_3_,3);
          release_string_ref(stack_locals + 1);
          exception_state = 0xffffffff;
          release_string_ref(&difficulty_settings_ptr);
        }
      }
    }
  }
  ExceptionList = saved_exception_list;
  return;
}

