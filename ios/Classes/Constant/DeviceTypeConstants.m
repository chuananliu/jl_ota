#import <TargetConditionals.h>

#if !defined(SWIFT_PACKAGE) || !TARGET_OS_SIMULATOR
//
//  DeviceTypeConstants.m
//  Runner
//
//  Created by 李放 on 2025/9/12.
//

#import "DeviceTypeConstants.h"

NSString *const DeviceTypeSoundBox = @"sound box";
NSString *const DeviceTypeChargingBin = @"charging box";
NSString *const DeviceTypeTWS = @"TWS";
NSString *const DeviceTypeHeadset = @"headset";
NSString *const DeviceTypeSoundCard = @"sound card";
NSString *const DeviceTypeWatch = @"watch";
NSString *const DeviceTypeTradition = @"tradition";

#endif
