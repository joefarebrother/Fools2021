# Fools 2021

My code for solving the hacking challenges of [TheZZAZZGlitch's Fools 2021 event](http://fools2021.online/index.php) - a minigame created with a custom Pokémon Red save file.

Disclaimer: Don't expect any of this code to be good.

This readme contains a writup of how I solved stuff.

## General 

I had the pokered sym file from a build of [Pokered](https://github.com/pret/pokered), which I added to each time I came across a function or memory location that was used by the game, and removed anything from the base game that got in the way and was unused. The sym file is [here](/fools.sym); my additions are at the bottom.

## Challenge 1

The challenge was to walk a large number of steps in any direction. I knew the game had to store the global player coordinates somewhere, so I walked around while looking at `wXCoord` and noticed pretty quickly that it would jump to `0x1f` whenever it would go below `0x10` and vice versa. So I set an access breakpoint here to find the code responsible, reverse engineered it a bit, and found that it was incrementing/decrementing 16-bit values`XChunk` and `YChunk` - and that the world must be divided into 16x16 chunks. 
So then I set my X coordinate to `0x7fff` and got the achievement. 

## Challenge 2

The next challenge was to reverse engineer to password system to unlock an otherwise inaccessible achievement. You get given a password when you select the "retire" option in the start menu. So I set a breakpoint where I'd found the start menu to be, reverse enguneered my way through the text rendering engine, and eventually found my way to `0xB77C`, at which point it looked like it was checking various achievemtn conditions (pikachu's HP, whether the pokedex is full, etc) and using them to set bits of the `e` register. I also notices that bit 3 was specifically reset. So, I set e to `0x0F` just after this point, enabling all the achievemnt flags, and got a password that completed the challenge I didn't actually look into the password encryption function itself at this point.

## Challenge 3

Now we get to the hard stuff. This challenge was to find the seed which generates the screenshot in the challenge description at the spawn point. The seed is a 32 bit value, the only thing knwn about it is that the last hex digit is `1` - leaving 28 bits worth of information. With a few access preakpoints I found the chunk generation code, and slowly managed to reverse engineer it and re-implement it [in python](/worldgen.py) [warning: bad code ahead], checking as I went that whet I was generating matched the data the game was actually generating. Well, I didn't actually convert the entire function, and left out the handling for biomes other than biome 0; which is OK since the target image is in biome 0 anyway.

My first plan was to simply brute-force all possible seeds. However, after runnign it for a bit I calculated that it would take me 18 hours to finish searching the adress space. I had 2 computers availiable, so I could cut that down to 9 hours pretty easily, but I assumed there must be a better way. An optimisation I was making was to only generate the central chunk, check it against the target image, and only if it matched its part then to generate the surrounding chunks. I'm not sure how effective this optimization was, however. I also logged "interesting seeds" in which the first chunk matched the target image, hoping to find some common property of them, to no avail.

In fact, NieDzejkob on discord said that he had a solution that ran in about 10 minutes on an emulator (so, without reimplementing the code) so I knew there was a better way. While waiting for my bruteforcer to finish, I tried staring at stuff trying to find a weakness in the custom RNG system (which was the key to a challenge of the fools2019 event) to no avail, while also reverse engineering more of the save. 

Eventually, my bruteforcer finished... with no results. I'm not exactly sure why - I had assumed it was to do with making incorrect assumptions about the tiles I could only see half of in the target images - some could either be ground tiles or half-tree-half-ground tiles, but I had innitially assumed them to be full ground tiles. However, when I eventually got the correct solution later, they *did* turn out to be full ground tiles. So I'm not sure what happened.
Anyway, I decided that without having found the weakness, I needed to rewrite it in a faster language. I'm not really a big fan of C, but I do rather like Rust, and I haven't written that much Rust code before, so I figured this would be a good opotunity. [So I rewrote it in Rust](/src/main.rs), cleaning up some of the messy parts, and this time allowing for the unknown tiles to be either possibility, Compiled it in release mode (which not only was fastest, but was necassary for integer overflow to work as I wanted - I know there's `wrapping_add` functions, but I couldn;t be bothered to use them) set it running. I was expecting it to be significantly faster than Python, but I didn't expect it to get through the *entire* search space in 10-15 minutes! It didn't find any results the first time, but I quickly found why (had mistyped the taret image) and set it running again, this time finding the correct answer in just 5 minutes! 

### Probably intended method

I then asked NieDzejkob what his method was, and he replied that the seed is generated using 4 consecutive calls to the `Random` runction in the same frame, and thus there weren't actually 2^28 possible seeds but rather 2^16, if you assume that the target seed was generated at random by the game rather than entered manually using the easter egg of holding select when the save file is loaded. Which it turns out it was.

This behaviour is because [Pokemon's randomness](https://github.com/pret/pokered/blob/2954013da1f10e11db4ec96f9586b7c01706ae1a/engine/math/random.asm) is determined by 3 bytes - `hRandomAdd`, `hRandomSub`, and `rDiv`; and only whether the addition involving `hRandomAdd` carries is relevant per call, making it effectively only contribute 4 bits of entropy. This means there are 2^20 seeds, or 2^16 seeds that end in a `1`. It's also why in the base game [some DV (called IV in later gens) combinations](https://www.youtube.com/watch?v=BcIxMyf8yHY) aren't possible for wild pokémon encounters, coincidentally including all those that would become shiny when transfered to gen 2.

Clever, but I never would have found this solution as I was looking in the wrong place, mainly trying to break the custom RNG function.

## Challenge 4

The final boss. This challenge was to find ACE and submit a working TAS demonstrating it. Well, I'd never founce ACE by myself before, and I'd never made a TAS before. So this was a real test of skill. The only bug I knew of in this version of the save file (although there was another unintended bug in an earlier version that would have made this easier) was mentioned by someone on the discord, that if you have 39 items in your inventory and then open it, the game crashes. I looked into it, and determied the couse of it, but it didn't look that useful. I also found that with 40 items, it doesn't crash but instead corrupts the map, due to writing a bunch of `FF00` throughout memory. 

I reverse engineered as much as I could, not finding any other obvious bugs, and came back to this one. I noticed something interesting; that when you had 40 items, the ending `FF` terminator is overwritten by a music byte, which was interesting. I checked what happened whan picking up an item in this state, and found that it continues searching through memory until it finds a byte that it interprets as an item id that matches that of the item you're collecting, and increments the next byte, interpreting it as an item quantity. 

So I write some quick python code to determine what interesting memory locations I could manipulate this way (i.e. which item-quantity bytes that were less than 99 and are proceeded by an item ID that's a real item - i.e. from `0x01` to `0x12`) - and discovered that two such locations were some code that was part of the password generation function. I figured this part at least must be intended - why else would that function even be in memory rather than the save file? It doesn't need to access another bank or anything. 

Next, I looked into the consequences of manipulating these bytes. Of course, they had a maximum value of `99` = `0x63`, so I couldn't get set them to `jp` and be done with it. I found that setting `0xdb74` to a 1-byte-argument instrution like `ld d, XX` cuased there to be a `ld sp, hl` inctruction in the final routine, which was very interesting as `hl` at this point points to the password bytes which could somewhat manipulated. And setting `0xdb7e` to a 2-byte-argument instruction like `ld hl, XXXX` would cause there to be a `dec sp` instruction. 

I wrote some Python to explore the different possible permutations of what I could do to manipulate the stack after this routine returns, and after several false leads and miscalculations later (one route idea even would have required me to wait for over 200 hours to manipulate the in-game timer!), I finally had a reasonable plan:

- I would use a seed that starts with `C382B8__`, which is asm for `jp B882`; the ACE target routine
- I would use 8 sharp beaks / sharp horns to raise the attack modifier to `0x18` (corresponding to a `jr` instruction)
- I would encoutner certain pokémon, and make sure to avoid certain other pokémon, to manipulate the first byte of the pokédex flags, which sits just after the attack modifier in memory, thus setting the argument of the above jump instruction to point to the seed (in fact, a couple of bytes before the seed into the Y chunk coordinate, due to constrainsts on what sets of pokémon are possible)
- The hard part: I would fill up my entire inventory by collecting lots of 99 stacks of a certain item (which ended up being shyhorn, but in my first draft of the plan was glitch shard due to constraints on what pokémon I could encounter) plus as many other unique items as possible; by grinding lots of encounters. I did all the bosses fot their uniqe items, including the last one which I thought dropped an item but didn't, but it was later pointed out to me that beating the last boss still is neccassary because otherwise there would be an `0x04` byte in memory (for number of bosses done) messing up the next step.
- Then I would collect 6 revival seeds and 1 bravery potion to manipulate the above mentioned memory locations
- Finally, I'd stand in a chunk in which the last byte of the chunk RNG for the last chunk loaded in memory was `0x76`, and use the ritere option. I had written some python, adapting my map generation code, to find a suitable seed in which such a chunk is close to the spawn and at a Y coordinate that doesn't cause problems: it was `C382B829`.

Now, when the password encryption routine returns, the stack pointer points to a byte before the password, and it returns to `0x2976`, which contains `call Bankswitch` - i.e. a fancy `jp hl`. `hl` at this point points just after the password, and execution will now slide down into the `jr` instruction I'd placed and reach the seed, thus jumping to the target routine. 

### TASing it

Now it was time to TAS the above plan. I defeinitely needed some form of automation for the part on filling my inventory. I originally was going to use [BizHawk](https://github.com/TASVideos/BizHawk), but then I noticed that the readme mentioned that Lua scripting is only supported in the windows version. So instead I used [Lsnes](http://tasvideos.org/Lsnes.html), which I could barely find any information about at all on the internet besides this little wiki page. Apparently it can run natively on Linux but I didn't know that so run the provided windows version through WINE, and it worked fine. 

Here's some of the stuff I figured out about it:
Load my ROM with File > Load > ROM
- To bind gameboy controls, I go configure > settings > controllers and bing each GB button to a keyboard button
- To use savestates, I go configure > settings > hotkeys, and bind controls for load > slot <n> and save > slot <n> - I bound save slots 1 to 9 to my number keys, with shift held to save and shift not held to load. The "slot select" options didn't seem to work.
- I then had to go File > Save > Change Working Directory to set the working directory for it to load lua scripts from, File > New > Project to set the directory it would save states to, and File > New > Movie to create a movie that starts from the reqired save file (SRAM). 
- There's a console that accepts commands that are breifly documented in the manual. Of particular usefulness to me were `run-lua <filename>` to load a lua script, `L <code>` to run inline Lua code, and `reset-lua` to reset the lua VM in case something goes wrong. 

Now, I was ready to start making the TAS. The first thing I did was write [some Lua code](/lsnes%20tas/veiw.lua) to display important memory locations on screen. One thing that tripped me up was that lsnes adresses memory by reletive adresses into regions like "WRAM", rather than with absolute adresses like the gameboy uses - so I wrote [a utility function](/lsnes%20tas/utils.lua#L33) to convert an absolute adress to a reletive one so I could just use absolute adresses everywhere. 

Next, I wrote [some RNG manipulation code](/lsnes%20tas/rng,lua) to manipulate items. It basically sets a save state, waits a number of frames, collects the item, and of it's the wrong one it re-loads from the savestate and increases the number of frames to wait.

I also tried to write a general encounter manipulation function (so I could walk around freely with no encounters and then also manipulate encounters when I need them) but couldn;t get it to work. So instead I made a more basic encounter farming function that would walk around until it got an encounter, and reload a savestate if it was the wrong one. 

Finally, putting it all together, I executed my route, running the automated item farming at 10x speed. Unfortunately, lsnes crashed due to running out of memory about 4-5 times. The first of these was while I'd left it running overnight, but the rest of them I was awake to reset the emulator and load the latest savestate to continue each time. 

Right near the end I encountered a problem which lead me to discovering the intended solution, but for now I managed to work around the problem and finish the run, reaching ACE and finally finishing the challenge. The TAS was about 32 hours long in total!

### The problem and the intended solution

When my inventory had finally reached 39 items, instead of new shyhorns going into the 40th slot, they would just "disapear" (really, corrupting something further on in memory), even though there was still an `FF` terminator in the 40th slot, rather than the terminator being overriten by the busic byte in the 41st slot. I looked into the reason why, and it turns out to be a bug in the base game with item handling, known as [the 99 item stack glitch](https://www.youtube.com/watch?v=OXzQ9rEEa0g). When recieving an item, when you have 99 of that item in your last inventory slot, the game skips over the next slo when looking for a terminator. 

Normally, I didn't encounter this because the game puts a ton of `0xff00` terminators into the inventory whenever you look at it, so when one is skipped over the item adding function still sees the next one, but the terminator in slot 40 is the last of these and thus skipping it does corrupt the memory ahead instead. 

I solved this by first collecting enough glitch shards to fill up my existing glitch shard slot and get an item into slot 40, from which point onwards I could continue my originally planned route. Except, I just so happened to have collected enough additional shyhorns that the chunk generation table had been corrupted such that the chunk I was supposed to stand in was now a solid block of trees! Fortunately, I could solve this by collecting enough additional shyhorns to create an entrance to that chunk - and fortunately this didn't intefer with the chunk-random value of `0x76` that I needed to have. (this value is for othe last chunk loaded in memory, rather than the one we actually stant in)

Now, that leads to the intended solution: The additional `0xFF00` terminators are only placed when you open your inventory, which I did and so never ran into this bug until the end. However, if you don't, then you could collect 99 revival seeds and then a few more to manipualte `0xDB74` without having to fill up the entire inventory. Same can be done for collecting a little over 99 bravery potions, though there are certainly possible routes that avoid that, too. (Stranck was working on one but unfortunately didn't manage to finish before the deadline). This method also opens up a little bit more space for manipulability of the password - as the first byte before encryption, the number of minutes passed, is no longer locked to `0xFF` as this can easily be done in much less than 255 minutes. 

This is almost certainly the intended solution. The challenge description even mentions the engine being built on top of the notoriously buggy pokémon red engine and thus hints at the intended bug actually being in the base game itself. 

## Conclusion 

As always, this event was very enjoyable. Thank you very much to TheZZAZZGlitch for putting on these events each year, you are a very awesome and cool person.