
/* WARNING: Type propagation algorithm not settling */
/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */
/* game_or_level_state 3 4 5 are active states where it can occur 6 is special case where no rescue
   happens

   // USE 1: Set to global constant threshold
   attempt_count_or_activation_threshold_l = DAT_00502afc;

   // USE 2: Compared against rescue attempt counter
   if (rescuebot_state_struct->rescue_attempt_counter_l <
       attempt_count_or_activation_threshold_l)

   // USE 3: Reused as pointer to difficulty settings
   attempt_count_or_activation_threshold_l = &difficulty_level_likely;
   piVar5 = (int *)*puVar1;
   if (piVar5 != &difficulty_level_likely) {
       attempt_count_or_activation_threshold_l = piVar5;
   } */

void __fastcall rescuebot_main ? (struct_rescuebot rescuebot_state_l)

{
    undefined4 *puVar1;
    void *pvVar2;
    undefined4 uVar3;
    int split_max_victim_or_game_state;
    uint uVar4;
    int *piVar5;
    struct_rescuebot *rescuebot_state_struct;
    int extraout_ECX;
    int extraout_ECX_00;
    ulonglong uVar6;
    char *pcVar7;
    int iVar8;
    int *attempt_count_or_activation_threshold_l;
    int local_80[29];
    void *local_c;
    undefined1 *puStack_8;
    undefined4 local_4;
    struct_game_world *pvVar5;

    local_4 = 0xffffffff;
    puStack_8 = &LAB_004d097b;
    local_c = ExceptionList;
    if ((char)rescuebot_state_struct->is_active_l != '\0')
    {
        pvVar5 = (struct_game_world *)DAT_00503a78[0xc];
        attempt_count_or_activation_threshold_l = DAT_00502afc;
        if (pvVar5->game_or_level_state_l != 6)
        {
            ExceptionList = &local_c;
            if ((rescuebot_state_struct->has_victim_l != 0) &&
                (ExceptionList = &local_c,
                 rescuebot_state_struct->current_location_id_or_dropoff_point_l < DAT_00502afc))
            {
                ExceptionList = &local_c;
                check_level_complete_and_activate_exits(pvVar5);
                puVar1 = FUN_00401290(local_80 + 7, "rescue\\RescueBot.cpp", 0x3c);
                local_4 = 0;
                FUN_004a3a19(puVar1 + 7, "RESCUEBOT: Victim dropped off");
                FUN_00401360(puVar1, 3);
                local_4 = 0xffffffff;
                FUN_004012c0(local_80 + 7);
                rescuebot_state_struct->has_victim_l = 0;
                FUN_00454130((int)rescuebot_state_struct);
                FUN_00454100(extraout_ECX);
            }
            if ((rescuebot_state_struct->has_victim_l == 0) &&
                (((split_max_victim_or_game_state = pvVar5->game_or_level_state_l,
                   split_max_victim_or_game_state == 3 || (split_max_victim_or_game_state == 4)) ||
                  (split_max_victim_or_game_state == 5))))
            {
                if (DAT_00502a78 != '\0')
                {
                    FUN_00402790(local_80, "DBG_ACTIVATE_RESCUEBOT");
                    piVar5 = local_80;
                    local_4 = 1;
                    pvVar2 = (void *)FUN_00499cb0(DAT_00503a78);
                    uVar3 = FUN_00438550(pvVar2, piVar5);
                    local_4 = 0xffffffff;
                    FUN_00401c90(local_80);
                    if ((char)uVar3 != '\0')
                    {
                        rescuebot_state_struct->rescue_attempt_counter_l =
                            (int *)((int)attempt_count_or_activation_threshold_l + 1);
                    }
                }
                if (rescuebot_state_struct->rescue_attempt_counter_l <
                    attempt_count_or_activation_threshold_l)
                {
                    local_80[1] = 0;
                    local_80[2] = 0;
                    local_80[3] = 0;
                    local_80[4] = 0x3fd00000;
                    local_80[5] = 0x9999999a;
                    local_80[6] = 0x3fd99999;
                    uVar6 = FUN_004b9400();
                    split_max_victim_or_game_state = (int)uVar6;
                    if (pvVar5->active_victim_count_l < split_max_victim_or_game_state)
                    {
                        find_assign_victim((int)rescuebot_state_struct);
                    }
                    else
                    {
                        puVar1 = FUN_00401290(local_80 + 7, "rescue\\RescueBot.cpp", 100);
                        iVar8 = 3;
                        pcVar7 = " victims";
                        local_4 = 2;
                        pvVar2 = (void *)FUN_0040c2f0(puVar1, "RESCUEBOT: Exceeded maximum of ");
                        pvVar2 = (void *)FUN_00412130(pvVar2, split_max_victim_or_game_state);
                        pvVar2 = (void *)FUN_0040c2f0(pvVar2, pcVar7);
                        FUN_00401360(pvVar2, iVar8);
                        local_4 = 0xffffffff;
                        FUN_004012c0(local_80 + 7);
                    }
                    FUN_004541a0((int)rescuebot_state_struct);
                }
                if (rescuebot_state_struct->message_timer_l < attempt_count_or_activation_threshold_l)
                {
                    uVar4 = rescuebot_hash_function(*(uint *)(rescuebot_state_struct->message_data_ptr_l + 4));
                    puVar1 = (undefined4 *)FUN_00412ed0(&rescuebot_state_struct->message_data_ptr_l, uVar4);
                    if (difficulty_init_likely == '\0')
                    {
                        difficulty_init_likely = '\x01';
                        difficulty_level_likely = 2;
                        DAT_0050190c = 0;
                        _DAT_00501910 = 1;
                        DAT_00501914 = 0;
                    }
                    attempt_count_or_activation_threshold_l = &difficulty_level_likely;
                    piVar5 = (int *)*puVar1;
                    if (piVar5 != &difficulty_level_likely)
                    {
                        *piVar5 = *piVar5 + 1;
                        attempt_count_or_activation_threshold_l = piVar5;
                    }
                    local_4 = 3;
                    piVar5 = get_bot_name(local_80 + 5);
                    local_4._0_1_ = 4;
                    pvVar2 = FUN_00412340(local_80 + 3, "^(128,128,240)", piVar5);
                    local_4._0_1_ = 5;
                    FUN_00403e40(pvVar2, local_80 + 1, ":\n^(255,255,255)");
                    local_4._0_1_ = 8;
                    FUN_00401c90(local_80 + 3);
                    local_4._0_1_ = 7;
                    FUN_00401c90(local_80 + 5);
                    FUN_00401d00(local_80 + 1, (char *)(attempt_count_or_activation_threshold_l + 3));
                    FUN_004574b0((void *)(DAT_00503a78[0xc] + 0x5f4), &attempt_count_or_activation_threshold_l);
                    FUN_00454130((int)rescuebot_state_struct);
                    FUN_00454100(extraout_ECX_00);
                    local_4 = CONCAT31(local_4._1_3_, 3);
                    FUN_00401c90(local_80 + 1);
                    local_4 = 0xffffffff;
                    FUN_00401c90(&attempt_count_or_activation_threshold_l);
                }
            }
        }
    }
    ExceptionList = local_c;
    return;
}
